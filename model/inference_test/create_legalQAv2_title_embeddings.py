import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from openai import OpenAI
import time
from tqdm import tqdm

# 환경 변수 로드
env_path = Path('..') / '.env'
load_dotenv(env_path)

# OpenAI 클라이언트 설정
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# MongoDB 연결
mongo_client = MongoClient(os.getenv('MONGODB_ATLAS_CLUSTER_URI'))
db = mongo_client['HelloWorld-AI']
collection = db['foreigner_legalQA_v2']  # 컬렉션 이름 수정

def create_embedding(text):
    """텍스트를 임베딩 벡터로 변환"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"임베딩 생성 중 에러 발생: {e}")
        return None

def process_documents():
    """모든 문서를 처리하여 임베딩 생성 및 저장"""
    documents = list(collection.find({}))
    success_count = 0
    error_count = 0
    
    print(f"총 처리할 문서 수: {len(documents)}")
    
    for doc in tqdm(documents, desc="문서 처리 중"):
        try:
            # title 필드에서 텍스트 추출
            title_text = doc.get('title', '').strip()
            
            if title_text:
                embedding = create_embedding(title_text)
                
                if embedding:
                    # 문서 업데이트: Embedding 필드에 직접 저장
                    collection.update_one(
                        {'_id': doc['_id']},
                        {
                            '$set': {
                                'Embedding': embedding
                            }
                        }
                    )
                    success_count += 1
                    time.sleep(0.5)  # API 속도 제한 고려
            
        except Exception as e:
            print(f"\n문서 {doc['_id']} 처리 중 에러 발생: {e}")
            error_count += 1

    return success_count, error_count

def main():
    try:
        print("임베딩 처리 시작...")
        success, errors = process_documents()
        print(f"\n처리 완료!")
        print(f"성공: {success}개")
        print(f"실패: {errors}개")
        
    except Exception as e:
        print(f"실행 중 에러 발생: {e}")
    
    finally:
        mongo_client.close()

if __name__ == "__main__":
    main()