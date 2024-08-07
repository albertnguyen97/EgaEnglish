import re
import json

def read_file(file_path):
    """Đọc nội dung từ file văn bản."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def parse_questions(content):
    """Phân tích nội dung văn bản và chuyển đổi thành danh sách câu hỏi."""
    questions = []
    # Tách các khối câu hỏi dựa trên tiêu đề phần
    parts = re.split(r'\n(?=PHẦN\s+[IVXLC]+\.)', content.strip())
    print(f"Phần văn bản được phân tách: {len(parts)} phần")

    for part in parts:
        part_title = re.match(r'^PHẦN\s+[IVXLC]+\.\s*(.*)', part, re.IGNORECASE)
        if part_title:
            print(part_title)
            part_number = part_title.group(0).strip()  # Lấy tiêu đề phần
            part_content = part[len(part_title.group(0)):].strip()
            # Tách các khối câu hỏi trong phần
            question_blocks = re.split(r'\n(?=\s*Câu\s*\d+)', part_content)

            for block in question_blocks:
                lines = block.split('\n')
                question_match = re.match(r'^\s*Câu\s*(\d+):\s*(.+)', lines[0])
                if question_match:
                    question_number = question_match.group(1).strip()
                    full_question_text = question_match.group(2).strip()
                    question_text_lines = [full_question_text]

                    # Xác định loại câu hỏi dựa trên tiêu đề phần
                    if "PHẦN I." in part_number:
                        question_type = "Nhiều Lựa chọn"
                    elif "PHẦN II." in part_number:
                        question_type = "Đúng/Sai"
                    elif "PHẦN III." in part_number:
                        question_type = "Trả lời ngắn"
                    else:
                        question_type = "Không xác định"

                    for line in lines[1:]:
                        if re.match(r'^\s*[A-Da-d][\.\)]\s*', line):
                            break
                        question_text_lines.append(line.strip())

                    # Xử lý ảnh (nếu có)
                    question_text = ' '.join(question_text_lines).strip().split('Ảnh')[0].strip()
                    img_text = None
                    if 'Ảnh' in ' '.join(question_text_lines).strip():
                        img_text = ' '.join(question_text_lines).strip().split('Ảnh', 1)[1].strip()
                        # print(f"Ảnh: {img_text}")

                    # Xử lý tùy chọn đáp án
                    options = {}
                    current_option = None
                    current_option_text = ""

                    for line in lines[1:]:
                        option_match = re.match(r'^\s*([A-Da-d])[\.\)]\s*(.*)', line)
                        if option_match:
                            if current_option:
                                options[current_option] = current_option_text.strip()
                            current_option = option_match.group(1).strip()
                            current_option_text = option_match.group(2).strip()
                        elif current_option:
                            current_option_text += ' ' + line.strip()

                    if current_option:
                        options[current_option] = current_option_text.strip()

                    options = {k: re.split(r'\s*PHẦN', v)[0].strip() for k, v in options.items()}
                    print(question_type)
                    questions.append({
                        "question_number": question_number,
                        "question": question_text,
                        "type": question_type,
                        "options": options,
                        "img": img_text
                    })

                elif re.match(r'^\s*Câu\s*(\d+)\.\s*(.*)', lines[0]):

                    question_match = re.match(r'^\s*Câu\s*(\d+)\.\s*(.*)', lines[0])
                    if question_match:
                        question_number = question_match.group(1).strip()
                        full_question_text = question_match.group(2).strip()
                        for line in lines[1:]:
                            full_question_text += line.strip() + ' '
                        question_text = full_question_text.split('*Ảnh*')[0].strip()
                        # print(question_text)
                        img_text = None
                        if '*Ảnh*' in full_question_text:
                            img_text = full_question_text.split('*Ảnh*', 1)[1].strip()
                            img_text = img_text.split(' ')[2].strip()

                        questions.append({
                            "question_number": question_number,
                            "question": question_text,
                            "type": "Trả lời ngắn",
                            "img": img_text,
                        })

    return questions


def save_to_json(data, output_file):
    """Lưu dữ liệu vào file JSON."""
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def process_questions(input_file, output_file):
    """Quy trình xử lý: đọc nội dung, phân tích câu hỏi và lưu vào file JSON."""
    content = read_file(input_file)
    questions = parse_questions(content)
    save_to_json(questions, output_file)
    print(f"Đã lưu {len(questions)} câu hỏi hợp lệ vào {output_file}")

# Đường dẫn tới file văn bản chứa các câu hỏi
input_file = 'output1.txt'
# Đường dẫn tới file JSON sẽ lưu trữ các câu hỏi
output_file = 'questions1.json'

# Chạy quy trình
process_questions(input_file, output_file)












