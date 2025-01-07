import streamlit as st
import google.generativeai as genai
import os, tempfile, time

# Hàm tạo và cập nhật file chat
def page_setup():
    # Cấu hình layout rộng cho ứng dụng Streamlit
    st.set_page_config(page_title="Chat with video files", layout="wide")  # Sử dụng layout "wide" cho giao diện rộng hơn

    # Thêm CSS để tối ưu không gian
    st.markdown(
        """
        <style>
            .reportview-container {
                max-width: 100% !important;  # Giúp giao diện chiếm toàn bộ màn hình
            }
            .sidebar .sidebar-content {
                width: 300px !important;  # Điều chỉnh độ rộng thanh sidebar nếu cần
            }
            #MainMenu {visibility: hidden;}  # Ẩn menu chính
            .sidebar {visibility: hidden;}   # Ẩn thanh sidebar nếu không cần thiết
        </style>
        """,
        unsafe_allow_html=True
    )

    # Tiêu đề trang
    st.header("Chat with video files!", anchor=False, divider="blue")

def main():
    page_setup()

    # Khởi tạo session_state để lưu câu hỏi và câu trả lời
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    # Fixed LLM settings
    model = "gemini-1.5-flash"
    temperature = 0.7  # Fixed temperature
    top_p = 0.9  # Fixed top_p
    max_tokens = 1500  # Fixed maximum tokens
    
    video_file_name = st.file_uploader("Upload your video", type=['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'])

    if video_file_name:
        # Tạo một tệp tạm thời để lưu nội dung video
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(video_file_name.read())  # Ghi nội dung video vào tệp tạm
            temp_file_path = temp_file.name  # Lưu lại đường dẫn tạm thời của tệp

        # Upload video sử dụng đường dẫn tạm thời với mime_type chỉ định
        mime_type = 'video/mp4'  # default to mp4, customize based on file type
        file_extension = video_file_name.name.split('.')[-1].lower()

        # Adjust mime type for different formats
        if file_extension == 'avi':
            mime_type = 'video/x-msvideo'
        elif file_extension == 'mov':
            mime_type = 'video/quicktime'
        elif file_extension == 'mkv':
            mime_type = 'video/x-matroska'
        elif file_extension == 'flv':
            mime_type = 'video/x-flv'
        elif file_extension == 'wmv':
            mime_type = 'video/x-ms-wmv'

        # Bắt đầu upload file
        video_file = genai.upload_file(path=temp_file_path, mime_type=mime_type)

        # Đợi quá trình tải lên hoàn tất
        while video_file.state.name == "PROCESSING":
            time.sleep(10)
            video_file = genai.get_file(video_file.name)
        if video_file.state.name == "FAILED":
            raise ValueError(video_file.state.name)

        # Giao diện song song cho người dùng
        col1, col2 = st.columns([6, 4])  # Cột 1 lớn hơn, chiếm 2/3, cột 2 chiếm 1/3

        with col1:
            # Display video trực tiếp trong Streamlit
            st.video(temp_file_path)

            # Phần nhập prompt của người dùng
            st.subheader("Chat with the video content")
            prompt3 = st.text_input("Enter your prompt.")
            if prompt3:
                # Gọi mô hình LLM Gemini 1.5 để tạo nội dung từ video dựa trên prompt
                model_instance = genai.GenerativeModel(model_name=model)
                st.write("Making LLM inference request...")
                response = model_instance.generate_content([video_file, prompt3], request_options={"timeout": 600})
                st.markdown(response.text)

                # Lưu câu hỏi và câu trả lời vào session_state
                st.session_state['history'].append((prompt3, response.text))

        with col2:
            st.subheader("Summary and Key Moments")
            # Hiển thị trạng thái đang tải
            st.write("Generating summary and key moments...")

            # Hai default prompt: một cho summary và một cho key moments
            summary_prompt = "Summarize the video content."
            key_moments_prompt = "List the key moments from the video."

            # Gọi LLM cho phần tóm tắt video
            model_instance = genai.GenerativeModel(model_name=model)
            summary_response = model_instance.generate_content([video_file, summary_prompt], request_options={"timeout": 600})

            # Gọi LLM cho các key moments
            key_moments_response = model_instance.generate_content([video_file, key_moments_prompt], request_options={"timeout": 600})

            # Kiểm tra nội dung phản hồi
            video_summary = summary_response.text if hasattr(summary_response, 'text') else "No summary available"
            key_moments = key_moments_response.text if hasattr(key_moments_response, 'text') else "No key moments available"

            # Hiển thị tóm tắt
            st.write("### Summary:")
            st.markdown(video_summary)

            # Xử lý key moments để loại bỏ dòng trắng thừa
            st.write("### Key Moments:")
            moments_list = [moment.strip() for moment in key_moments.split('\n') if moment.strip()]  # Loại bỏ dòng trống
            for moment in moments_list:
                st.markdown(f"- {moment}")

            # Hiển thị lịch sử câu hỏi và câu trả lời
            st.subheader("Question and Answer History")
            for i, (q, a) in enumerate(st.session_state['history']):
                st.write(f"**Q{i+1}:** {q}")
                st.write(f"**A{i+1}:** {a}")
                st.write("---")

        # Xóa tệp video đã tải lên
        genai.delete_file(video_file.name)
        print(f'Deleted file {video_file.uri}')

if __name__ == '__main__':
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY_NEW')
    genai.configure(api_key=GOOGLE_API_KEY)
    main()
