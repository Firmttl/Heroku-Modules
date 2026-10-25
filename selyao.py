"""
    🌸 Celestian Relation Automator (Selyao)
"""

__version__ = (2, 6, 0)
# meta developer: @FirmTTL
# meta description: Автоматизация отношений Селестиан: обычные и VIP уровни, мониторинг и остановка задач

import asyncio
import logging
import random
import re
import time

from .. import loader, utils

try:
    from herokutl.tl.types import Message
except ImportError:
    from herokutl.types import Message

logger = logging.getLogger(__name__)


@loader.tds
class SelyaoMod(loader.Module):
    """Автоматизация отношений Селестиан с мониторингом задач (Обычные + VIP)"""

    strings = {
        "name": "SelyaoManager",
        "_cls_doc": "Automation of Celestian relations (regular + VIP levels) with task monitoring.",
        "started": "🚀 <b>Protocol started ({})!</b>\nID: <code>{}</code>\nLevel: <code>{}</code>\nAction: <i>{}</i>\nCount: <code>{}</code>",
        "finished": "✅ <b>Cycle finished ({})!</b>\nCompleted <code>{}</code> actions: <i>{}</i>",
        "error": "❌ <b>Usage:</b> <code>.selyao [lvl/viplvl] [count]</code>\nExample VIP: <code>.selyao vip1 5</code> or <code>.selyao v1 5</code>",
        "bad_count": "❌ <b>Count must be an integer from 1 to {}.</b>",
        "bad_level": "❌ <b>Level not found (available 1-30).</b>",
        "bad_vip_level": "❌ <b>VIP level not found (available 1-30).</b>",
        "duplicate": "⚠️ Task <code>{}</code> with the same mode is already running in this chat.",
        "send_error": "❌ <b>Failed to send message:</b> {}",
        "no_tasks": "ℹ️ <b>No running processes.</b>",
        "list_header": "📊 <b>Running relation processes:</b>\n\n",
        "list_item": "🔹 <code>{}</code> [{}] | Done: <code>{}/{}</code>\n⏳ Next in: <code>{}</code>\n",
        "stop": "🛑 <b>Task <code>{}</code> stopped.</b>",
        "stop_all": "🛑 <b>All tasks in this chat stopped.</b>",
        "stop_none": "❌ Task ID not found.",
        "cfg_max_count": "Max actions per task",
        "cfg_jitter": "Random delay add-on (sec)",
        "cfg_notify": "Notify in Saved Messages on finish",
        "cfg_no_dup": "Refuse duplicate tasks in one chat",
    }

    strings_ru = {
        "_cls_doc": "Автоматизация отношений Селестиан (обычные + VIP уровни) с мониторингом задач.",
        "started": "🚀 <b>Запуск протокола ({})!</b>\nID: <code>{}</code>\nУровень: <code>{}</code>\nДействие: <i>{}</i>\nКоличество: <code>{}</code>",
        "finished": "✅ <b>Цикл завершен ({})!</b>\nВыполнено <code>{}</code> действий: <i>{}</i>",
        "error": "❌ <b>Ошибка:</b> Используй <code>.selyao [lvl/viplvl] [кол-во]</code>\nПример VIP: <code>.selyao vip1 5</code> или <code>.selyao v1 5</code>",
        "bad_count": "❌ <b>Количество должно быть числом от 1 до {}.</b>",
        "bad_level": "❌ <b>Уровень не найден (доступно 1-30).</b>",
        "bad_vip_level": "❌ <b>VIP уровень не найден (доступно 1-30).</b>",
        "duplicate": "⚠️ Задача <code>{}</code> с таким режимом уже запущена в этом чате.",
        "send_error": "❌ <b>Не удалось отправить сообщение:</b> {}",
        "no_tasks": "ℹ️ <b>Нет запущенных процессов.</b>",
        "list_header": "📊 <b>Запущенные процессы отношений:</b>\n\n",
        "list_item": "🔹 <code>{}</code> [{}] | Сделано: <code>{}/{}</code>\n⏳ След. через: <code>{}</code>\n",
        "stop": "🛑 <b>Процесс <code>{}</code> остановлен.</b>",
        "stop_all": "🛑 <b>Все процессы этого чата остановлены.</b>",
        "stop_none": "❌ ID не найден.",
        "cfg_max_count": "Макс. действий на задачу",
        "cfg_jitter": "Случайная добавка к задержке (сек)",
        "cfg_notify": "Уведомление в «Избранное» по завершении",
        "cfg_no_dup": "Запрет дублей задач в одном чате",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "max_count", 50, lambda: self.strings("cfg_max_count"),
                validator=loader.validators.Integer(minimum=1, maximum=500),
            ),
            loader.ConfigValue(
                "jitter", 15, lambda: self.strings("cfg_jitter"),
                validator=loader.validators.Integer(minimum=0, maximum=300),
            ),
            loader.ConfigValue(
                "notify", True, lambda: self.strings("cfg_notify"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "no_duplicates", True, lambda: self.strings("cfg_no_dup"),
                validator=loader.validators.Boolean(),
            ),
        )

        # Обычные уровни (1-30)
        self.levels = {
            1: (".отн сделать комплимент", 3 * 60 + 15),
            2: (".отн Сделать завтрак", 5 * 60 + 12),
            3: (".отн Подарить цветы", 7 * 60 + 9),
            4: (".отн Посмотреть фильм", 9 * 60 + 45),
            5: (".отн Сделать массаж", 13 * 60),
            6: (".отн Романтический ужин", 19 * 60 + 30),
            7: (".отн Сделать подарок", 24 * 60 + 42),
            8: (".отн Туристическая поездка", 29 * 60 + 15),
            9: (".отн Вечер астрономии", 39 * 60),
            10: (".отн Приятные воспоминания", 52 * 60),
            11: (".отн Совместная фотосессия", 58 * 60 + 30),
            12: (".отн Создать традицию", 65 * 60),
            13: (".отн Совместный проект", 71 * 60),
            14: (".отн Исследовать родословную", 78 * 60),
            15: (".отн Спланировать будущее", 84 * 60),
            16: (".отн Исполнить желание", 91 * 60),
            17: (".отн Годовщина отношений", 97 * 60),
            18: (".отн Обустроить жилище", 104 * 60),
            19: (".отн Духовное единение", 110 * 60),
            20: (".отн Уединенный отдых", 117 * 60),
            21: (".отн Написать клятву", 130 * 60),
            22: (".отн Создать талисман", 143 * 60),
            23: (".отн Написать песню", 156 * 60),
            24: (".отн Вырастить сад", 169 * 60),
            25: (".отн Танцевальный вечер", 182 * 60),
            26: (".отн Семейный совет", 195 * 60),
            27: (".отн Назвать звезду", 208 * 60),
            28: (".отн Написать книгу", 221 * 60),
            29: (".отн Организовать праздник", 234 * 60),
            30: (".отн Вечная любовь", 260 * 60),
        }

        # VIP уровни (1-30) — слово "вип" полностью убрано из отправляемого текста
        self.vip_levels = {
            1: (".отн Аура эмпатии", 3 * 60 + 15),
            2: (".отн Нейронная связь", 5 * 60 + 12),
            3: (".отн Параллельный мир", 7 * 60 + 9),
            4: (".отн Днк любовь", 9 * 60 + 45),
            5: (".отн Квантовое слияние", 13 * 60),
            6: (".отн Голограмма чувств", 19 * 60 + 30),
            7: (".отн Антигравитационный танец", 24 * 60 + 42),
            8: (".отн Хроносинхронизация", 29 * 60 + 15),
            9: (".отн Космическая медитация", 39 * 60),
            10: (".отн Мультивселенская симуляция", 52 * 60),
            11: (".отн Телепатическое послание", 58 * 60 + 30),
            12: (".отн Энергетический резонанс", 65 * 60),
            13: (".отн Биолюминесцентное слияние", 71 * 60),
            14: (".отн Психосоматический симбиоз", 78 * 60),
            15: (".отн Метаморфоза среды", 84 * 60),
            16: (".отн Трансцендентальное переживание", 91 * 60),
            17: (".отн Астральное путешествие", 97 * 60),
            18: (".отн Нексус сознаний", 104 * 60),
            19: (".отн Сингулярность чувств", 110 * 60),
            20: (".отн Вечная квантовая запутанность", 117 * 60),
            21: (".отн Сверхновая связь", 130 * 60),
            22: (".отн Темпоральное святилище", 143 * 60),
            23: (".отн Межпространственная резонансная камера", 156 * 60),
            24: (".отн Алхимия душ", 169 * 60),
            25: (".отн Абсолютная гармония", 182 * 60),
            26: (".отн Бесконечная итерация любви", 195 * 60),
            27: (".отн Квинтэссенция бытия", 208 * 60),
            28: (".отн Панкосмическое сознание", 221 * 60),
            29: (".отн Омега-точка слияния", 234 * 60),
            30: (".отн Божественная унификация", 260 * 60),
        }

        self.active_tasks = {}
        self._client = None

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        self.active_tasks = {}

    async def on_unload(self):
        for data in list(self.active_tasks.values()):
            data["stop"].set()
            handle = data.get("handle")
            if handle is not None:
                handle.cancel()
        self.active_tasks.clear()

    @staticmethod
    def _get_time_str(seconds):
        if seconds <= 0:
            return "отправка..."
        if seconds < 60:
            return f"{int(seconds)} сек."
        return f"{int(seconds // 60)} мин. {int(seconds % 60)} сек."

    @staticmethod
    def _parse_level(raw_lvl):
        digits = re.sub(r"\D", "", raw_lvl)
        if not digits:
            return None, False
        return int(digits), raw_lvl.startswith("vip") or raw_lvl.startswith("v")

    @staticmethod
    def _new_task_id(active_tasks):
        while True:
            task_id = f"ID{random.randint(100, 999)}"
            if task_id not in active_tasks:
                return task_id

    async def _runner(self, task_id, chat_id, cmd_text, count, delay):
        data = self.active_tasks.get(task_id)
        if data is None:
            return

        jitter = int(self.config["jitter"])

        try:
            for _ in range(count):
                if task_id not in self.active_tasks or data["stop"].is_set():
                    return

                try:
                    await self._client.send_message(chat_id, cmd_text)
                except Exception as e:
                    logger.exception(e)
                    secs = getattr(e, "seconds", 0) or 0
                    pause = max(int(secs), 5)
                    data["next_run"] = time.time() + pause
                    try:
                        await asyncio.wait_for(data["stop"].wait(), timeout=pause)
                        return
                    except asyncio.TimeoutError:
                        continue

                data["sent"] += 1
                if data["sent"] >= count:
                    break

                wait_time = delay + (random.randint(0, jitter) if jitter > 0 else 0)
                data["next_run"] = time.time() + wait_time
                try:
                    await asyncio.wait_for(data["stop"].wait(), timeout=wait_time)
                    return
                except asyncio.TimeoutError:
                    pass

            if (
                task_id in self.active_tasks
                and not data["stop"].is_set()
                and self.config["notify"]
            ):
                await self._client.send_message(
                    "me", self.strings("finished").format(data["mode"], count, cmd_text)
                )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(e)
            try:
                await self._client.send_message(
                    chat_id, self.strings("send_error").format(utils.escape_html(str(e)))
                )
            except Exception:
                logger.exception(e)
        finally:
            self.active_tasks.pop(task_id, None)

    @loader.command(ru_doc="<lvl / vip[lvl]> <count> — запустить цикл (обычный или VIP)")
    async def selyaocmd(self, message: Message):
        """Start relations cycle: .selyao <level> <count>"""
        args = utils.get_args(message)
        if len(args) < 2:
            return await utils.answer(message, self.strings("error"))

        max_count = int(self.config["max_count"])
        try:
            count = int(args[1])
        except ValueError:
            return await utils.answer(
                message, self.strings("bad_count").format(max_count)
            )

        if not 1 <= count <= max_count:
            return await utils.answer(
                message, self.strings("bad_count").format(max_count)
            )

        lvl_num, is_vip = self._parse_level(args[0].lower().strip())
        if lvl_num is None:
            return await utils.answer(message, self.strings("error"))

        if is_vip:
            if lvl_num not in self.vip_levels:
                return await utils.answer(message, self.strings("bad_vip_level"))
            cmd_text, delay = self.vip_levels[lvl_num]
            mode_name = f"VIP {lvl_num}"
        else:
            if lvl_num not in self.levels:
                return await utils.answer(message, self.strings("bad_level"))
            cmd_text, delay = self.levels[lvl_num]
            mode_name = f"Обычный {lvl_num}"

        if self.config["no_duplicates"]:
            for tid, d in self.active_tasks.items():
                if d["chat"] == message.chat_id and d["mode"] == mode_name:
                    return await utils.answer(
                        message, self.strings("duplicate").format(tid)
                    )

        task_id = self._new_task_id(self.active_tasks)
        stop_event = asyncio.Event()
        self.active_tasks[task_id] = {
            "mode": mode_name,
            "cmd": cmd_text,
            "total": count,
            "sent": 0,
            "next_run": 0,
            "chat": message.chat_id,
            "stop": stop_event,
            "handle": None,
        }

        await utils.answer(
            message,
            self.strings("started").format(
                mode_name, task_id, lvl_num, cmd_text, count
            ),
        )

        self.active_tasks[task_id]["handle"] = asyncio.create_task(
            self._runner(task_id, message.chat_id, cmd_text, count, delay)
        )

    @loader.command(ru_doc="— список запущенных процессов")
    async def slistcmd(self, message: Message):
        """List running tasks"""
        if not self.active_tasks:
            return await utils.answer(message, self.strings("no_tasks"))

        res = self.strings("list_header")
        for tid, d in self.active_tasks.items():
            wait = d["next_run"] - time.time()
            res += self.strings("list_item").format(
                tid, d["mode"], d["sent"], d["total"], self._get_time_str(wait)
            )
        await utils.answer(message, res)

    @loader.command(ru_doc="[ID] — остановить задачу")
    async def sstopcmd(self, message: Message):
        """Stop task: .sstop <ID>"""
        args = utils.get_args(message)
        if not args:
            to_stop = [
                tid for tid, d in self.active_tasks.items()
                if d["chat"] == message.chat_id
            ]
            if not to_stop:
                return await utils.answer(message, self.strings("no_tasks"))

            for tid in to_stop:
                data = self.active_tasks.pop(tid, None)
                if data is not None:
                    data["stop"].set()
            return await utils.answer(message, self.strings("stop_all"))

        tid = args[0].upper()
        if tid not in self.active_tasks and f"ID{tid}" in self.active_tasks:
            tid = f"ID{tid}"

        data = self.active_tasks.pop(tid, None)
        if data is None:
            return await utils.answer(message, self.strings("stop_none"))

        data["stop"].set()
        await utils.answer(message, self.strings("stop").format(tid))
