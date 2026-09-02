import random
import time
from concurrent.futures import ThreadPoolExecutor


def generate_number(prefix, length):
    suffix = ''.join(str(random.randint(1, 9)) for _ in range(length))
    return prefix + suffix


def main():
    prefix = input("Nhập prefix: ")
    amount = int(input("Nhập số lượng số muốn random: "))
    suffix_length = int(input("Nhập số lượng số phía sau prefix: "))
    filename=input('Nhập filename(có đuôi nếu có): ')
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=amount) as executor:
        results = list(
            executor.map(
                lambda _: generate_number(prefix, suffix_length),
                range(amount)
            )
        )

    with open(f"{filename}", "a", encoding="utf-8") as file:
        file.write("\n")
        file.write("\n".join(results))
    
    elapsed = time.time() - start_time
    speed = amount / elapsed if elapsed > 0 else amount
    print()
    print(f"Speed: {speed:.2f} số/giây")
    print()
    print(f"Random completed, {amount} results have been saved to {filename}")


if __name__ == "__main__":
    main()