input_file = input('Tên file(có loại tệp nếu có): ')
suffix=int(input('Nhập suffix thường[0] hay sđt[1]: '))
suffix_check=False
output_file = input_file

if suffix==0:
    suffix_check=True
    suffix_input=input('Nhập suffix: ')
else:
    suffix_check=False

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []

for line in lines:
    text = line.strip()

    if text and ":" not in text and suffix_check==False:
        text = f"{text}:{text}"

    if text and ":" not in text and suffix_check==True:
        text = f"{text}:123456"

    new_lines.append(text + "\n")

with open(output_file, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print()

print(f"Đã xử lý xong! Kết quả được lưu trong {output_file}")