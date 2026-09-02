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
    filename = input("Nhập filename(có đuôi nếu có): ")

    start_time = time.time()

    results = set()

    # Kiểm tra khả năng tạo đủ số khác nhau
    max_unique = 9 ** suffix_length

    if amount > max_unique:
        print(f"Không thể tạo {amount} số không trùng.")
        print(f"Tối đa chỉ có thể tạo {max_unique} số khác nhau.")
        return

    with ThreadPoolExecutor(max_workers=min(amount, 100)) as executor:
        while len(results) < amount:
            needed = amount - len(results)

            new_results = executor.map(
                lambda _: generate_number(prefix, suffix_length),
                range(needed)
            )

            results.update(new_results)

    results = list(results)

    with open(filename, "a", encoding="utf-8") as file:
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
