import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import io
import os
from urllib.parse import urljoin, quote

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("bbcf_move_query", "AstrBot Plugin Developer", "查询BBCF游戏角色招式数据并渲染为图片", "1.0.0")
class BBCFMoveQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_url = "https://www.dustloop.com/w/BBCF"
        self.session = None

    async def initialize(self):
        """插件初始化"""
        self.session = aiohttp.ClientSession()
        logger.info("BBCF招式查询插件已初始化")

    async def terminate(self):
        """插件销毁"""
        if self.session:
            await self.session.close()
        logger.info("BBCF招式查询插件已停止")

    @filter.command("查")
    async def query_move(self, event: AstrMessageEvent):
        """查询BBCF角色招式数据，格式：查 角色名 招式指令"""
        try:
            # 解析用户输入
            message_str = event.message_str.strip()
            match = re.match(r'^查\s+(\w+)\s+([a-zA-Z0-9]+)$', message_str)
            
            if not match:
                yield event.plain_result("格式错误！请使用：查 角色名 招式指令\n例如：查 es 5b")
                return
            
            character = match.group(1).lower()
            move = match.group(2).lower()
            
            # 查询招式数据
            move_data = await self.get_move_data(character, move)
            
            if move_data:
                # 渲染为图片
                image_bytes = await self.render_move_image(move_data, character, move)
                if image_bytes:
                    yield event.image_result(image_bytes)
                else:
                    yield event.plain_result("图片渲染失败")
            else:
                yield event.plain_result(f"未找到角色 {character} 的招式 {move} 的数据")
                
        except Exception as e:
            logger.error(f"查询招式数据时发生错误: {e}")
            yield event.plain_result(f"查询失败：{str(e)}")

    async def get_move_data(self, character: str, move: str):
        """从dustloop获取招式数据"""
        try:
            # 构建角色页面URL
            character_url = f"{self.base_url}/{character.capitalize()}"
            
            # 设置超时时间
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with self.session.get(character_url, timeout=timeout) as response:
                if response.status != 200:
                    logger.error(f"无法访问角色页面: {character_url}, 状态码: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 查找招式表格
                move_data = self.parse_move_table(soup, move)
                if move_data:
                    return move_data
                
                # 如果没找到，尝试在其他页面查找
                return await self.search_move_in_other_pages(character, move)
                
        except asyncio.TimeoutError:
            logger.error(f"请求超时: {character_url}")
            return None
        except Exception as e:
            logger.error(f"获取招式数据时发生错误: {e}")
            return None

    def parse_move_table(self, soup, move):
        """解析招式表格"""
        try:
            # 查找包含招式数据的表格
            tables = soup.find_all('table', {'class': ['wikitable', 'movetable']})
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # 检查第一列是否包含我们要找的招式
                        first_cell = cells[0].get_text(strip=True).lower()
                        if move.lower() in first_cell:
                            move_data = {
                                'move': cells[0].get_text(strip=True),
                                'damage': self.extract_cell_data(cells, 'damage', '伤害'),
                                'guard': self.extract_cell_data(cells, 'guard', '防御'),
                                'startup': self.extract_cell_data(cells, 'startup', '发生'),
                                'active': self.extract_cell_data(cells, 'active', '持续'),
                                'recovery': self.extract_cell_data(cells, 'recovery', '恢复'),
                                'frame_adv': self.extract_cell_data(cells, 'frame_adv', 'frame', '有利'),
                                'cancel': self.extract_cell_data(cells, 'cancel', '取消'),
                                'properties': self.extract_cell_data(cells, 'properties', '属性')
                            }
                            return move_data
            
            return None
            
        except Exception as e:
            logger.error(f"解析招式表格时发生错误: {e}")
            return None

    def extract_cell_data(self, cells, *keywords):
        """从单元格中提取特定数据"""
        try:
            for cell in cells[1:]:  # 跳过第一个单元格（招式名称）
                cell_text = cell.get_text(strip=True).lower()
                for keyword in keywords:
                    if keyword.lower() in cell_text:
                        return cell.get_text(strip=True)
            return "N/A"
        except:
            return "N/A"

    async def search_move_in_other_pages(self, character: str, move: str):
        """在其他页面搜索招式"""
        try:
            # 尝试访问框架数据页面
            framedata_url = f"{self.base_url}/{character.capitalize()}/Frame_Data"
            
            # 设置超时时间
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with self.session.get(framedata_url, timeout=timeout) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    return self.parse_move_table(soup, move)
            
            return None
            
        except asyncio.TimeoutError:
            logger.error(f"请求超时: {framedata_url}")
            return None
        except Exception as e:
            logger.error(f"在其他页面搜索招式时发生错误: {e}")
            return None

    async def render_move_image(self, move_data, character, move):
        """将招式数据渲染为图片"""
        try:
            # 创建图片
            width, height = 600, 400
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # 尝试使用系统字体
            try:
                # 在Linux系统中尝试使用中文字体
                font_paths = [
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                    '/System/Library/Fonts/Arial.ttf',  # macOS
                    'C:/Windows/Fonts/arial.ttf'  # Windows
                ]
                title_font = None
                regular_font = None
                
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        title_font = ImageFont.truetype(font_path, 24)
                        regular_font = ImageFont.truetype(font_path, 18)
                        break
                
                if title_font is None:
                    title_font = ImageFont.load_default()
                    regular_font = ImageFont.load_default()
                    
            except Exception:
                title_font = ImageFont.load_default()
                regular_font = ImageFont.load_default()
            
            # 绘制标题
            title = f"{character.upper()} - {move.upper()} 招式数据"
            draw.text((50, 30), title, fill='black', font=title_font)
            
            # 绘制招式数据
            y_offset = 80
            line_height = 35
            
            data_items = [
                ("招式", move_data['move']),
                ("伤害", move_data['damage']),
                ("防御类型", move_data['guard']),
                ("发生帧", move_data['startup']),
                ("持续帧", move_data['active']),
                ("恢复帧", move_data['recovery']),
                ("帧优势", move_data['frame_adv']),
                ("取消", move_data['cancel']),
                ("属性", move_data['properties'])
            ]
            
            for label, value in data_items:
                # 绘制标签
                draw.text((50, y_offset), f"{label}:", fill='black', font=regular_font)
                # 绘制值
                draw.text((200, y_offset), value, fill='blue', font=regular_font)
                y_offset += line_height
            
            # 添加来源信息
            draw.text((50, height - 30), "数据来源: dustloop.com", fill='gray', font=regular_font)
            
            # 转换为字节
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"渲染图片时发生错误: {e}")
            return None