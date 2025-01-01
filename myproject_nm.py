import streamlit as st
import google.generativeai as genai
import os, tempfile, time

def page_setup():
    st.header("Chat with video files!", anchor=False, divider="blue")

    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

def main():
    page_setup()

    # Fixed LLM settings
    model = "gemini-1.5-flash"  # Fixed model
    temperature = 0.7  # Fixed temperature
    top_p = 0.9  # Fixed top_p
    max_tokens = 1500  # Fixed maximum tokens
    
    video_file_name = st.file_uploader("Upload your video", type=['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'])

    if video_file_name:
        # Tạo một tệp tạm thời để lưu nội dung video
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(video_file_name.read())  # Ghi nội dung video vào tệp tạm
            temp_file_path = temp_file.name  # Lưu lại đường dẫn tạm thời của tệp

        # Display video trực tiếp trong Streamlit
        st.video(temp_file_path)

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

        video_file = genai.upload_file(path=temp_file_path, mime_type=mime_type)

        # Đợi quá trình tải lên hoàn tất
        while video_file.state.name == "PROCESSING":
            time.sleep(10)
            video_file = genai.get_file(video_file.name)
        if video_file.state.name == "FAILED":
            raise ValueError(video_file.state.name)

        # Nhận đầu vào từ người dùng
        prompt3 = st.text_input("Enter your prompt.")
        if prompt3:
            # Gọi mô hình LLM Gemini 1.5 để tạo nội dung từ video
            model_instance = genai.GenerativeModel(model_name=model)
            st.write("Making LLM inference request...")
            response = model_instance.generate_content([video_file, prompt3], request_options={"timeout": 600})
            st.markdown(response.text)

        # Xóa tệp video đã tải lên
        genai.delete_file(video_file.name)
        print(f'Deleted file {video_file.uri}')


if __name__ == '__main__':
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY_NEW')
    genai.configure(api_key=GOOGLE_API_KEY)
    main()
