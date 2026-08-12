import time
import requests

class TorrentStreamer:
    def __init__(self, magnet_link):
        self.magnet_link = magnet_link
        self.video_file_path = None
        self.is_ready = False
        self.qb_url = "http://localhost:8080"
        self.session = requests.Session()

    def start_streaming(self):
        import threading
        thread = threading.Thread(target=self._connect_to_qb, daemon=True)
        thread.start()

    def _connect_to_qb(self):
        try:

            login_data = {"username": "admin", "password": "adminadmin"}
            login_res = self.session.post(f"{self.qb_url}/api/v2/auth/login", data=login_data)

            if login_res.text == "Fails.":
                print("Ошибка: Неверный логин или пароль от qBittorrent!")
                return


            self.session.post(f"{self.qb_url}/api/v2/torrents/add", data={"urls": self.magnet_link})
            print("Торрент добавлен. Ожидание метаданных торрента...")


            time.sleep(2)
            r = self.session.get(f"{self.qb_url}/api/v2/torrents/info")
            torrents = r.json()
            if not torrents:
                print("Список торрентов пуст.")
                return

            target_torrent = torrents[-1]
            torrent_hash = target_torrent['hash']


            self.session.post(f"{self.qb_url}/api/v2/torrents/toggleSequentialDownload", data={"hashes": torrent_hash})
            self.session.post(f"{self.qb_url}/api/v2/torrents/toggleFirstLastPiecePrio", data={"hashes": torrent_hash})


            files = []
            retries = 30
            while retries > 0:
                r_files = self.session.get(f"{self.qb_url}/api/v2/torrents/files?hash={torrent_hash}")
                if r_files.status_code == 200:
                    files = r_files.json()
                    if files:
                        break
                time.sleep(1)
                retries -= 1

            if not files:
                print("Ошибка: qBittorrent не смог получить метаданные.")
                return

            video_file = max(files, key=lambda x: x['size'])
            print(f"Найдено видео: {video_file.get('name', 'Без имени')}")

            file_id = video_file.get('id') if video_file.get('id') is not None else video_file.get('index')


            stream_url = f"{self.qb_url}/proxy/torrent/{torrent_hash}/file/{file_id}"


            print("Буферизация первых кусков видео...")
            stream_retries = 30
            while stream_retries > 0:
                try:
                    # Делаем HEAD запрос, чтобы не качать сам файл скриптом, а просто проверить статус
                    # Передаем куки авторизации в заголовках, так как прокси может требовать сессию
                    check = self.session.head(stream_url, timeout=2)
                    if check.status_code == 200:
                        print("Сервер готов к отдаче потока!")
                        break
                except Exception:
                    pass
                time.sleep(1)
                stream_retries -= 1

            self.video_file_path = stream_url
            self.is_ready = True
            print(f"Стрим запущен: {self.video_file_path}")

        except Exception as e:
            print(f"Ошибка стриминга: {e}")
