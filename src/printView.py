from typing import List

import tiktoken
from langchain.document_loaders import Docx2txtLoader, UnstructuredPowerPointLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
from tqdm import tqdm
import os

import openai
from langchain import PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
#from langchain.embeddings.huggingface import HuggingFaceEmbeddings #https://github.com/BM-K/Sentence-Embedding-is-all-you-need
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.docstore.document import Document

from readPDF import PDFReader
from promptTemplate import loadTemplate
from quoteChecker import change_quote_num, print_quote

class PrintAssetView:
    def __init__(self,
                 llmAiEngine:str = 'gpt-3.5-turbo',
                 temperature:float = 0.0,
                 temperature_s:float = 0.5,
                 temperature_agg:float = 1.0,
                 ):
        self.pr = PDFReader()
        self.templates = loadTemplate()
        #tokenizer = tiktoken.get_encoding("cl100k_base")
        self.tokenizer = tiktoken.encoding_for_model(llmAiEngine)  # "gpt-4"도 가능

        self.PROMPT = PromptTemplate(template=self.templates['template'], input_variables=["summaries", "question"])
        self.PROMPT_S = PromptTemplate(template=self.templates['template_s'], input_variables=["summaries", "question"])
        self.PROMPT_AGG = PromptTemplate(template=self.templates['template_agg'], input_variables=["summaries", "question"])

        self.chain = load_qa_with_sources_chain(ChatOpenAI(model_name=llmAiEngine,
                                                      temperature=temperature,
                                                      frequency_penalty=0.0,
                                                      ), chain_type="stuff", prompt=self.PROMPT)
        self.chain_s = load_qa_with_sources_chain(ChatOpenAI(model_name=llmAiEngine,
                                                        temperature=temperature_s,
                                                        frequency_penalty=1.0,
                                                        ), chain_type="stuff", prompt=self.PROMPT_S)
        self.chain_agg = load_qa_with_sources_chain(ChatOpenAI(model_name=llmAiEngine,
                                                        temperature=temperature_agg,
                                                        frequency_penalty=0.0,
                                                        ), chain_type="stuff", prompt=self.PROMPT_AGG)

    def setting(
            self,
            apiKey        :str                                  ,
            filelist      :List                                  ,
            dbPath        :str  =None                           ,
            #embeddingAi   :str  ='BM-K/KoSimCSE-bert-multitask' ,
            docSize       :int  =500                              ,
            docOverlap    :int  =100                              ,
            ):
        '''
        기본 세팅을 위한 전처리 프로세스
        :param apiKey: OPEN AI에서 발급받은 api Key 입력
        :param filelist: 백데이터(pdf) 경로값
        :param embeddingAi: 임베딩에 사용할 hugging face 기반 ai의 directory
        :param docSeparator: PDF 문서를 분할하기 위한 분할자
        :param docSize: PDF 문서 분할 문장 단위
        :param docOverlap: PDF 문서 분할시 오버랩 문장수
        :return: langchain.vectorstores.chroma.Chroma 임베딩과 함께 저장된 Document 데이터베이스
        '''

        os.environ["OPENAI_API_KEY"] = apiKey
        openai.api_key = os.getenv("OPENAI_API_KEY")

        embeddings = OpenAIEmbeddings(openai_api_key=apiKey)
        #embeddings = HuggingFaceEmbeddings(model_name=embeddingAi)

        if dbPath is not None and os.path.isdir(dbPath):
            docsearch = Chroma(embedding_function=embeddings, persist_directory=dbPath+'/')
        else:
            listOfExt = list(set([file.split('.')[-1] for file in filelist]))

            docs_split = []
            for ext in listOfExt:
                split_filelist = [file for file in filelist if file.split('.')[-1] == ext]

                if ext == 'pdf':
                    pdftexts = self.pr.getPDF(filelist=split_filelist)


                    for doc in tqdm(pdftexts, desc='PDF 세부분할'):
                        doc_split = self.pr.split_text_byChunk(doc,
                                                              chunk_size=docSize,
                                                              overlap=docOverlap)
                        '''
                        doc_split= self.pr.split_text(doc,
                                              separator =docSeparator,
                                              size      =docSize,
                                              overlap   =docOverlap)
                        '''
                        docs_split.extend(doc_split)
                elif ext == 'doc' or ext == 'docx':
                    for file in split_filelist:
                        loader = Docx2txtLoader(file)
                        data = loader.load_and_split(CharacterTextSplitter(
                            chunk_size=docSize,
                            overlap = docOverlap
                        ))
                        docs_split.extend(data)
                elif ext == 'ppt' or ext == 'pptx':
                    for file in split_filelist:
                        loader = UnstructuredPowerPointLoader(file)
                        data = loader.load_and_split(CharacterTextSplitter(
                            chunk_size=docSize,
                            overlap = docOverlap
                        ))
                        docs_split.extend(data)
                elif ext == 'txt':
                    for file in split_filelist:
                        loader = TextLoader(file)
                        data = loader.load_and_split(CharacterTextSplitter(
                            chunk_size=docSize,
                            overlap = docOverlap
                        ))
                        docs_split.extend(data)
                else:
                    continue

            if dbPath is None:
                docsearch = Chroma.from_documents(docs_split, embeddings)
            else:
                docsearch = Chroma.from_documents(docs_split, embeddings, persist_directory=dbPath+'/')
                docsearch.persist()

        return docsearch

    def getSimilarDocs(self,
                       query: str,
                       baseDocument,
                       numberOfReason: int = 10,
                       ):
        '''
        쿼리와 유사한 Text Chunk를 찾는 프로세스
        :param query:
        :param baseDocument:
        :param numberOfReason:
        :return:
        '''
        docs = baseDocument.similarity_search(query, k=numberOfReason)

        return docs

    def printEvidence(
            self,
            query: str,
            docs,
    ):
        '''
        쿼리에 대한 근거를 생성하는 텍스트 컨센서스 생성 프로세스
        :param query:
        :param baseDocument:
        :param iterNum:
        :return:
        '''

        '''근거 목록 저장'''
        context_doc = []
        token_count = 0

        summ_docs_part = []
        doc_offset = 0
        doc_count = 0
        token_sub_count = 0
        for doc in docs:
            summ_docs_part.append(doc)
            doc_count += 1
            token_sub_count += len(self.tokenizer.encode(doc.page_content))

            '''요약하기 원하는 문서 토큰의 개수가 2048개 이상인 경우에만, 요약을 수행. 그 외에는 문서 모으는 작업만 수행'''
            if token_sub_count < 2048:
                pass
            else:
                output = self.chain({"input_documents": summ_docs_part, "question": query}, return_only_outputs=True)
                output['output_text'] = change_quote_num(output['output_text'], doc_offset)

                summ_docs_part = []
                doc_offset += doc_count
                doc_count = 0
                token_sub_count = 0

                '''요약을 완료한 문서의 토큰 개수가 2048개 이상인 경우에는 작업을 완전 중지'''
                context_doc.append(Document(page_content=output['output_text'], metadata={"source": ''}))
                token_count += len(self.tokenizer.encode(output['output_text']))
                if token_count >= 2048:
                    break

        '''작업을 완료한 이후, token count 조건이 충족되지 않았다면, 마지막으로 남은 문서를 요약하기 위해 추가 작업 수행'''
        if token_count == 0:
            output = self.chain({"input_documents": summ_docs_part, "question": query}, return_only_outputs=True)
            output['output_text'] = change_quote_num(output['output_text'], doc_offset)

            context_doc.append(Document(page_content=output['output_text'], metadata={"source": ''}))

        return context_doc

    def filterEvidence(self,
                       query: str,
                       context_doc,):
        '''
        쿼리에 대한 근거를 필터링 및 재정렬하는 텍스트 컨센서스 생성 프로세스
        :param query:
        :param context_doc:
        :return:
        '''
        '''필터링 근거 출력'''
        output = self.chain_s({"input_documents": context_doc, "question": query}, return_only_outputs=True)
        rearr_context_doc = Document(page_content=output['output_text'], metadata={"source": ''})
        # print(output['output_text'])

        return rearr_context_doc

    def printConclusion(
            self,
            query: str,
            rearr_context_doc,
    ):
        '''
        쿼리에 대한 응답을 생성하는 텍스트 컨센서스 생성 프로세스
        :param query:
        :param rearr_context_doc:
        :param docs:
        :return:
        '''

        '''요약 기준 결론 출력'''
        output = self.chain_agg({"input_documents": [rearr_context_doc], "question": query}, return_only_outputs=True)

        return output

    def printQuote(
            self,
            rearr_context_doc,
            docs,
    ):
        '''
        쿼리에 대한 응답을 생성하는 텍스트 컨센서스 생성 프로세스
        :param rearr_context_doc:
        :param docs:
        :return:
        '''

        '''주석 출력'''
        quoteOutput = print_quote(rearr_context_doc, docs, verbose=False)

        return quoteOutput