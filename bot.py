from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    TCPConnector,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from http.cookies import SimpleCookie
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils.conversions import to_hex
from base64 import urlsafe_b64decode
from datetime import datetime, timedelta, timezone
from colorama import *
import asyncio, random, time, json, sys, re, os

class WGA:
    def __init__(self) -> None:
        self.BASE_API = "https://api.wga.xyz"

        self.CAPTCHA = {
            "page_url": "https://wga.xyz/",
            "solver_api": "https://api.2captcha.com",
            "site_key": "0x4AAAAAAEBpKTZ7NKmH0K-Q",
            "captcha_key": None
        }

        self.REF_CODE = "C5R9L1R5"

        self.USE_PROXY = False
        self.ROTATE_PROXY = False
        
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.accounts = {}
        
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/117.0.0.0"
        ]

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Web3 Growth Agent {Fore.BLUE + Style.BRIGHT}Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        filename = "accounts.txt"
        try:
            with open(filename, 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            return accounts
        except Exception as e:
            print(f"{Fore.RED + Style.BRIGHT}Failed To Load Accounts: {e}{Style.RESET_ALL}")
            return None

    def load_captcha_key(self):
        filename = "captcha_key.txt"
        try:
            with open(filename, 'r') as file:
                captcha_key = file.readline().strip()
            self.CAPTCHA["captcha_key"] = captcha_key
            return captcha_key
        except FileNotFoundError:
            self.log(f"{Fore.RED}File {filename} Not Found.{Style.RESET_ALL}")
            return None

    def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"
    
    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return TCPConnector(ssl=False), None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return TCPConnector(ssl=False), clean_url, auth
            else:
                return TCPConnector(ssl=False), proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def display_proxy(self, proxy_url=None):
        if not proxy_url: return "No Proxy"

        proxy_url = re.sub(r"^(http|https|socks4|socks5)://", "", proxy_url)

        if "@" in proxy_url:
            proxy_url = proxy_url.split("@", 1)[1]

        return proxy_url

    def get_next_run_time(self, anchor_minute=1):
            now = datetime.now(timezone.utc)
            today_target = now.replace(hour=0, minute=anchor_minute, second=0, microsecond=0)
    
            if today_target > now:
                return today_target
            else:
                return today_target + timedelta(days=1)

    def extract_cookies(self, idx: int, response: object):
        existing = self.accounts[idx].get("cookies", {})
        
        jar = SimpleCookie()
        
        for k, v in existing.items():
            jar[k] = v
        
        for h in response.headers.getall("Set-Cookie", []):
            jar.load(h)
        
        self.accounts[idx]["cookies"] = {
            k: m.value for k, m in jar.items()
        }

        return self.accounts[idx]["cookies"]
    
    def initialize_headers(self, idx: int):
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Authorization": "Bearer",
            "Cache-Control": "no-cache",
            "Origin": "https://wga.xyz",
            "Pragma": "no-cache",
            "Referer": "https://wga.xyz/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.accounts[idx]["user_agent"]
        }

        return headers.copy()
    
    def generate_evm_wallet(self, idx: int, private_key: str):
        try:
            keypair = Account.from_key(private_key)
            address = keypair.address
            self.accounts[idx]["keypair"] = keypair
            self.accounts[idx]["address"] = address
            return address
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Generate Wallet Failed {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    def generate_signature(self, idx: int, message: str):
        try:
            keypair = self.accounts[idx]["keypair"]
            encoded_message = encode_defunct(text=message)
            signed_message = keypair.sign_message(encoded_message)
            signature = to_hex(signed_message.signature)
            return signature
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed: {str(e)}")

    def decode_token(self, idx: int):
        try:
            access_token = self.accounts[idx]["access_token"]
            header, payload, signature = access_token.split(".")
            decoded_payload = urlsafe_b64decode(payload + "==").decode("utf-8")
            parsed_payload = json.loads(decoded_payload)
            exp_time = parsed_payload["exp"]

            return exp_time
        except Exception as e:
            return None

    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None

    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = (
                        "With" if proxy_choice == 1 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    self.USE_PROXY = True if proxy_choice == 1 else False
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

        if self.USE_PROXY:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()
                if rotate_proxy in ["y", "n"]:
                    self.ROTATE_PROXY = True if rotate_proxy == "y" else False
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")
    
    async def ensure_ok(self, response):
        if response.status >= 400:
            error_text = await response.text()
            raise Exception(f"HTTP {response.status}: {error_text}")
    
    async def check_connection(self, proxy_url=None):
        url = "https://api.ipify.org?format=json"

        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url=url, proxy=proxy, proxy_auth=proxy_auth) as response:
                    await self.ensure_ok(response)
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None

    async def solve_turnstile(self, retries=5):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Captcha :{Style.RESET_ALL}")
        
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=ClientTimeout(total=60)) as session:
                    
                    if self.CAPTCHA["captcha_key"] is None:
                        self.log(
                            f"{Fore.BLUE + Style.BRIGHT}   Status  : {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}Captcha Key Is None{Style.RESET_ALL}"
                        )
                        return None

                    url = f"{self.CAPTCHA['solver_api']}/createTask"
                    data = json.dumps({
                        "clientKey": self.CAPTCHA["captcha_key"],
                        "task": {
                            "type": "TurnstileTaskProxyless",
                            "websiteURL": self.CAPTCHA["page_url"],
                            "websiteKey": self.CAPTCHA["site_key"],
                            "action": "reward_login"
                        }
                    })
                    async with session.post(url=url, data=data) as response:
                        await self.ensure_ok(response)
                        result_text = await response.text()
                        result_json = json.loads(result_text)

                        if result_json.get("errorId") != 0:
                            err_text = result_json.get("errorDescription", "Unknown Error")
                            
                            self.log(
                                f"{Fore.BLUE + Style.BRIGHT}   Message : {Style.RESET_ALL}"
                                f"{Fore.YELLOW + Style.BRIGHT}{err_text}{Style.RESET_ALL}"
                            )
                            await asyncio.sleep(5)
                            continue

                        task_id = result_json.get("taskId")
                        self.log(
                            f"{Fore.BLUE + Style.BRIGHT}   Task Id : {Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT}{task_id}{Style.RESET_ALL}"
                        )

                        for _ in range(30):
                            res_url = f"{self.CAPTCHA['solver_api']}/getTaskResult"
                            res_data = json.dumps({
                                "clientKey": self.CAPTCHA["captcha_key"],
                                "taskId": task_id
                            })
                            async with session.post(url=res_url, data=res_data) as res_response:
                                await self.ensure_ok(res_response)
                                res_result_text = await res_response.text()
                                res_result_json = json.loads(res_result_text)

                                if res_result_json.get("status") == "ready":
                                    recaptcha_token = res_result_json["solution"]["token"]
                                    self.log(
                                        f"{Fore.BLUE + Style.BRIGHT}   Status  : {Style.RESET_ALL}"
                                        f"{Fore.GREEN + Style.BRIGHT}Turnstile Solved Successfully{Style.RESET_ALL}"
                                    )
                                    return recaptcha_token
                                elif res_result_json.get("status") == "processing":
                                    self.log(
                                        f"{Fore.BLUE + Style.BRIGHT}   Message : {Style.RESET_ALL}"
                                        f"{Fore.YELLOW + Style.BRIGHT}Captcha Not Ready{Style.RESET_ALL}"
                                    )
                                    await asyncio.sleep(5)
                                    continue
                                else:
                                    break

            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.BLUE + Style.BRIGHT}   Status  : {Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT}Trunstile Not Solved{Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT}{str(e)}{Style.RESET_ALL}"
                )
                return None
    
    async def users_nonce(self, idx: int, turnstile_token: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/users/nonce"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(idx)
                headers["Content-Type"] = "application/json"
                payload = {
                    "address": self.accounts[idx]["address"],
                    "turnstileToken": turnstile_token,
                    "referrerInviteCode": self.REF_CODE,
                    "hp": "",
                    "elapsedMs": random.randint(10000, 15000),
                    "interacted": True
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Nonce {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def users_login(self, idx: int, message: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/users/login"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(idx)
                headers["Content-Type"] = "application/json"
                payload = {
                    "address": self.accounts[idx]["address"],
                    "signature": self.generate_signature(idx, message),
                    "referrerInviteCode": self.REF_CODE
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        self.extract_cookies(idx, response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def auth_refresh(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/auth/refresh"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(idx)
                headers["Content-Type"] = "application/json"
                cookies = self.accounts[idx].get("cookies", {})

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, cookies=cookies, json={}, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        self.extract_cookies(idx, response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Refresh :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def social_link_status(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/users/social-link-status"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(
                        url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Social  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Link Status {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None

    async def reward_status(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/users/reward-status"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(
                        url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Reward  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Status {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None

    async def daily_checkin(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/users/check-in"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None

    async def random_boxes(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/users/random-boxes"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(
                        url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Boxes   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Available Random Boxes {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None

    async def open_random_boxes(self, idx: int, box_id: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/users/random-boxes/{box_id}/open"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        if response.status == 401:
                            await self.process_auth_refresh(idx, proxy_url)
                            continue
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT}Box{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {box_id} {Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT}Failed to Open{Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT}{str(e)}{Style.RESET_ALL}"
                )

        return None

    async def process_check_connection(self, idx: int, proxy_url=None):
        while True:
            if self.USE_PROXY:
                proxy_url = self.get_next_proxy_for_account(idx)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.display_proxy(proxy_url)} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy_url)
            if is_valid: return True

            if self.ROTATE_PROXY:
                proxy_url = self.rotate_proxy_for_account(idx)
                await asyncio.sleep(1)
                continue

            return False
    
    async def process_auth_refresh(self, idx: int, proxy_url=None):
        refresh = await self.auth_refresh(idx, proxy_url)
        if not refresh: return False

        self.accounts[idx]["access_token"] = refresh.get("accessToken")
        self.accounts[idx]["exp_time"] = self.decode_token(idx)

        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Refresh :{Style.RESET_ALL}"
            f"{Fore.GREEN + Style.BRIGHT} Success {Style.RESET_ALL}"
        )

        return True

    async def process_user_login(self, idx: int, proxy_url=None):
        is_valid = await self.process_check_connection(idx, proxy_url)
        if not is_valid: return False

        if int(time.time()) > self.accounts[idx].get("exp_time", 0):

            if self.USE_PROXY:
                proxy_url = self.get_next_proxy_for_account(idx)

            if self.accounts[idx].get("cookies", {}):
                if not await self.process_auth_refresh(idx, proxy_url): return False
            else:
                turnstile_token = await self.solve_turnstile()
                if not turnstile_token: return False

                nonce = await self.users_nonce(idx, turnstile_token, proxy_url)
                if not nonce: return False

                message = nonce.get("message")

                login = await self.users_login(idx, message, proxy_url)
                if not login: return False

                self.accounts[idx]["access_token"] = login.get("accessToken")
                self.accounts[idx]["exp_time"] = self.decode_token(idx)

                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT} Success {Style.RESET_ALL}"
                )

        return True

    async def process_accounts(self, idx: int, proxy_url=None):
        logined = await self.process_user_login(idx, proxy_url)
        if not logined: return False

        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(idx)

        socials = await self.social_link_status(idx, proxy_url)
        if not socials: return False

        if all(item["status"] is None for item in socials["socialLinks"]):
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Social  :{Style.RESET_ALL}"
                f"{Fore.YELLOW + Style.BRIGHT} Connect Your X/TG Account First {Style.RESET_ALL}"
            )
            return False

        reward = await self.reward_status(idx, proxy_url)
        if reward:
            accumulated_xyz = reward.get("accumulatedXyz")
            checkin_available = reward.get("checkInAvailable")

            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Reward  :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {accumulated_xyz} XYZ {Style.RESET_ALL}"
            )

            if checkin_available:

                while True:
                    checkin = await self.daily_checkin(idx, proxy_url)
                    if checkin:
                        is_rewarded = checkin.get("rewarded")
                        box_issued = checkin.get("randomBoxIssued")

                        if is_rewarded and box_issued:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                                f"{Fore.GREEN + Style.BRIGHT} Success {Style.RESET_ALL}"
                            )
                            break

                        else:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                                f"{Fore.YELLOW + Style.BRIGHT} Success, But No Box Was Issued. Retrying Check-In in 1 minute. {Style.RESET_ALL}"
                            )
                            await asyncio.sleep(60)
                            continue

            else:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} Already Claimed {Style.RESET_ALL}"
                )

        random_boxes = await self.random_boxes(idx, proxy_url)
        if random_boxes:
            unopenned = random_boxes.get("unopenedCount")
            if unopenned == 0:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Boxes   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} No Openable Box Available {Style.RESET_ALL}"
                )
            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Boxes   :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} {unopenned} Openable {Style.RESET_ALL}"
                )

                issued_boxes = [b for b in random_boxes.get("boxes") if b.get("status") == "ISSUED"]
                for box_id in (b.get("id") for b in issued_boxes):
                    open = await self.open_random_boxes(idx, box_id, proxy_url)
                    if open:
                        reward = open.get("rewardAmount")

                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.BLUE+Style.BRIGHT}Box{Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT} {box_id} {Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT}Opened{Style.RESET_ALL}"
                            f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                            f"{Fore.BLUE+Style.BRIGHT}Reward:{Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT} {reward} XYZ {Style.RESET_ALL}"
                        )

    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                print(f"{Fore.RED+Style.BRIGHT}No Accounts Loaded.{Style.RESET_ALL}") 
                return

            self.load_captcha_key()
            self.print_question()

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if self.USE_PROXY: self.load_proxies()

                separator = "=" * 25
                for idx, private_key in enumerate(accounts, start=1):
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {idx} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {len(accounts)} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                    )

                    if idx not in self.accounts:
                        self.accounts[idx] = {
                            "user_agent": random.choice(self.USER_AGENTS)
                        }

                    wallet = self.generate_evm_wallet(idx, private_key)
                    if not wallet: continue

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Address :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.mask_account(self.accounts[idx]['address'])} {Style.RESET_ALL}"
                    )
                    
                    await self.process_accounts(idx)
                    await asyncio.sleep(random.uniform(2.0, 3.0))

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*60)
                
                next_run = self.get_next_run_time(anchor_minute=1)
                
                while True:
                    now = datetime.now(timezone.utc)
                    remaining = (next_run - now).total_seconds()

                    if remaining <= 0:
                        break

                    formatted_time = self.format_seconds(remaining)

                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed...{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)

        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = WGA()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Web3 Growth Agent - BOT{Style.RESET_ALL}                                       "                              
        )
        sys.exit(0)