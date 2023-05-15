from glob import glob
from os.path import join

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSettings

from printView import PrintAssetView

settings = QSettings("setting.ini", QSettings.IniFormat)
temp = PrintAssetView()

#help.ui dialog class 선언
class help(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('help.ui', self)
        self.show()

#화면을 띄우는데 사용되는 Class 선언
class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = None
        self.load_ui()

        self.dbPath = None
        self.docs = None

        self.load_config()

        self.btn_Gen_.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.btn_DB_.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.btn_Setting_.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))

        #btn_Help에 help.ui dialog를 띄움
        self.btn_Help.clicked.connect(lambda: help())

        self.save_config()

        self.setup_fr_Setting()
        self.setup_fr_DB()
        self.setup_fr_Gen()

    #config.ini 파일에서 설정값을 불러옴
    def load_config(self):
        self.line_key.setText(settings.value("OPENAI_API_KEY", ""))
        self.line_openaiM.setText(settings.value("GENERATOR_AI", ""))
        self.line_evid.setText(settings.value("NUM_EVIDENCE", ""))
        self.line_calc.setText(settings.value("NUM_EVIDENCE_PROC", ""))
        self.line_evidF.setText(settings.value("TEMP_EVIDENCE", ""))
        self.line_filterF.setText(settings.value("TEMP_FILTER", ""))
        self.line_concF.setText(settings.value("TEMP_CONCLUSION", ""))
        self.line_pdfPath.setText(settings.value("PDF_PATH", ""))
        self.line_chunkSize.setText(settings.value("CHUNKSIZE", ""))
        self.line_overlapSize.setText(settings.value("OVERLAPSIZE", ""))
        self.line_SaveLog.setText(settings.value("LOG_SAVE_PATH", ""))

    #값이 바뀔 때마다 config.ini 파일에 저장
    def save_config(self):
        #line_key에 값이 바뀌면 config.ini 파일에 저장
        self.line_key.textChanged.connect(
            lambda: settings.setValue("OPENAI_API_KEY", self.line_key.text())
        )

        #line_openaiM에 값이 바뀌면 config.ini 파일에 저장
        self.line_openaiM.textChanged.connect(
            lambda: settings.setValue("GENERATOR_AI", self.line_openaiM.text())
        )
        #line_evid에 값이 바뀌면 config.ini 파일에 저장
        self.line_evid.textChanged.connect(
            lambda: settings.setValue("NUM_EVIDENCE", self.line_evid.text())
        )
        #line_calc에 값이 바뀌면 config.ini 파일에 저장
        self.line_calc.textChanged.connect(
            lambda: settings.setValue("NUM_EVIDENCE_PROC", self.line_calc.text())
        )
        #line_evidF에 값이 바뀌면 config.ini 파일에 저장
        self.line_evidF.textChanged.connect(
            lambda: settings.setValue("TEMP_EVIDENCE", self.line_evidF.text())
        )
        #line_filterF에 값이 바뀌면 config.ini 파일에 저장
        self.line_filterF.textChanged.connect(
            lambda: settings.setValue("TEMP_FILTER", self.line_filterF.text())
        )
        #line_concF에 값이 바뀌면 config.ini 파일에 저장
        self.line_concF.textChanged.connect(
            lambda: settings.setValue("TEMP_CONCLUSION", self.line_concF.text())
        )
        #line_pdfPath에 값이 바뀌면 config.ini 파일에 저장
        self.line_pdfPath.textChanged.connect(
            lambda: settings.setValue("PDF_PATH", self.line_pdfPath.text())
        )
        #line_chunkSize에 값이 바뀌면 config.ini 파일에 저장
        self.line_chunkSize.textChanged.connect(
            lambda: settings.setValue("CHUNKSIZE", self.line_chunkSize.text())
        )
        #line_overlapSize에 값이 바뀌면 config.ini 파일에 저장
        self.line_overlapSize.textChanged.connect(
            lambda: settings.setValue("OVERLAPSIZE", self.line_overlapSize.text())
        )
        #line_SaveLog에 값이 바뀌면 config.ini 파일에 저장
        self.line_SaveLog.textChanged.connect(
            lambda: settings.setValue("LOG_SAVE_PATH", self.line_SaveLog.text())
        )

    def load_ui(self):
        self.ui = uic.loadUi('app.ui', self)
        self.show()

    '''#####################################
            컨센서스생성 Frame 생성 함수 목록
       #####################################'''

    def setup_fr_Gen(self):

        #query를 받아 컨센서스를 출력하는 버튼
        self.btn_Submit.clicked.connect(
            lambda: self.getText()
        )

        #btn_ClearLog를 누르면 text_Output을 초기화
        self.btn_ClearLog.clicked.connect(
            lambda: self.text_Output.clear()
        )

        #btn_SaveLog를 누르면 line_SaveLog 주소에 text_Output을 저장
        self.btn_SaveLog.clicked.connect(
            lambda: self.saveLog()
        )

    def saveLog(self):
        #line_SaveLog에 주소가 없으면 경고창 출력
        if self.line_SaveLog.text() == '':
            QMessageBox.about(self, '경고', '저장할 주소를 입력하세요.')
            return

        #line_SaveLog에 주소가 있으면 text_Output을 저장
        try:
            with open(f'{self.line_SaveLog.text()}/log.txt', 'w') as f:
                f.write(self.text_Output.toPlainText())
        except:
            QMessageBox.about(self, '경고', '저장할 주소를 다시 입력하세요.')
            return

    def makeDocs(self, query):
        #query를 받아 evidence를 출력
        docs = self.psv.getSimilarDocs(
            query=query,
            baseDocument=self.docsearch,
            numberOfReason=int(self.slider_evid.value()),
        )

        self.docs = docs

        return

    def printEvidence(self, query):
        #query를 받아 evidence를 출력
        evidence = self.psv.printEvidence(
            query=query,
            docs=self.docs,
            iterNum=int(self.slider_calc.value()),
        )

        self.evidence = evidence

        return

    def filterEvidence(self,query):
        #query를 받아 evidence를 출력
        evidenceFiltered = self.psv.filterEvidence(
            query=query,
            context_doc=self.evidence,
        )

        self.evidenceFiltered = evidenceFiltered

        #text_Output에 conclusion을 표시
        self.text_Output.append(str(evidenceFiltered.page_content))

        return

    def printConclusion(self, query):

        #query를 받아 conclusion을 출력
        conclusion = self.psv.printConclusion(
            query=query,
            rearr_context_doc=self.evidenceFiltered,
        )

        #text_Output에 conclusion을 표시
        self.text_Output.append(str(conclusion['output_text']))

        self.conclusion = conclusion

        return

    def printQuote(self):
        #query를 받아 quote를 출력
        quote = self.psv.printQuote(
            rearr_context_doc=self.evidenceFiltered,
            docs=self.docs,
        )

        #text_Output에 quote를 표시
        self.text_Output.append(''.join(quote))

        return

    def getText(self):

        #만약 docsearch가 없다면 경고창 출력
        if self.docsearch == None:
            QMessageBox.about(self, '경고', '[데이터베이스 관리]탭에서\nDB를 먼저 생성하세요.')
            return

        query = self.text_Query.toPlainText()
        QApplication.processEvents()

        self.evidence = None
        self.docs = None

        #text_Status에 진행상황(시작) 표시
        self.text_Status.setText('프로세스 시작 ')
        QApplication.processEvents()

        #text_Output에 query를 표시
        self.text_Output.append(f'\n[{query}]')
        QApplication.processEvents()

        #query와 유사한 문서 목록 출력
        self.text_Status.setText('유사문서 검색(1/4) ')
        self.makeDocs(query)
        QApplication.processEvents()

        #query를 받아 evidence를 출력
        self.text_Status.setText('근거문서 요약(2/4) ')
        self.printEvidence(query)
        QApplication.processEvents()

        #query를 받아 evidence 필터
        self.text_Status.setText('근거문서 필터(3/4) ')
        self.filterEvidence(query)
        QApplication.processEvents()

        #query를 받아 conclusion을 출력
        self.text_Status.setText('결론 출력(4/4) ')
        self.printConclusion(query)
        QApplication.processEvents()

        #query를 받아 quote를 출력
        self.printQuote()
        QApplication.processEvents()

        #text_Status에 진행상황(모든 과정 완료) 표시
        self.text_Status.setText('프로세스 완료 ')

        return

    '''#####################################
            데이터베이스관리 Frame 생성 함수 목록
       #####################################'''

    def setup_fr_DB(self):
        #toolButton_pdfPath를 누르면 QFileDialog를 띄워 pdfpath를 설정
        self.toolButton_pdfPath.clicked.connect(
            lambda: self.set_pdfPath()
        )

        #help_pdfPath tooltip 작성
        self.help_pdfPath.setToolTip(
            'pdf 파일이 저장된 폴더의 경로를 지정하세요.'
        )

        #btn_LoadPDF를 누르면 pdfpath에 있는 pdf를 table_pdf에 출려
        self.table_pdf.setRowCount(0)
        self.table_pdf.setColumnCount(2)
        self.table_pdf.setHorizontalHeaderLabels(['파일명', '파일경로'])
        self.btn_LoadPDF.clicked.connect(
            lambda: self.loadPDF()
        )

        #btn_genDB를 누르면 buildDB 함수 실행
        self.btn_genDB.clicked.connect(
            lambda: self.buildDB()
        )

        #slider_chunkSize의 값과 line_chunkSize를 연동
        self.slider_chunkSize.valueChanged.connect(
            lambda: self.line_chunkSize.setText(str(self.slider_chunkSize.value()))
        )
        self.line_chunkSize.textChanged.connect(
            lambda: self.slider_chunkSize.setValue(int(self.line_chunkSize.text()))
        )
        #help_chunkSize tooltip 작성
        self.help_chunkSize.setToolTip(
            'PDF파일 내 세부문서를 만들기 위해, 분할할 문장 단위를 지정하세요.'
        )

        # slider_overlapSize의 값과 line_overlapSize를 연동
        self.slider_overlapSize.valueChanged.connect(
            lambda: self.line_overlapSize.setText(str(self.slider_overlapSize.value()))
        )
        self.line_overlapSize.textChanged.connect(
            lambda: self.slider_overlapSize.setValue(int(self.line_overlapSize.text()))
        )
        #help_overlapSize tooltip 작성
        self.help_overlapSize.setToolTip(
            '세부문서를 만들 때, 중복을 허용할 문장 단위를 지정하세요.'
        )

        #delete key가 눌리면 table_pdf에서 선택된 row를 지우도록 설정
        self.table_pdf.keyPressEvent = self.deleteRow

        #drag and drop을 통해 table_pdf에 pdf를 추가
        self.table_pdf.setAcceptDrops(True)
        self.table_pdf.dropEvent = self.dropEvent
        self.table_pdf.dragMoveEvent = self.dragMoveEvent
        self.table_pdf.dragEnterEvent = self.dragEnterEvent

        return

    def dropEvent(self, event):
        #파일을 내려놓음
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(str(url.toLocalFile()))
            self.addPDF(links)
        else:
            event.ignore()
        return

    def dragMoveEvent(self, event):
        #drag 중인 이벤트를 감지
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()
        return

    def dragEnterEvent(self, event):
        #drag and drop에서 Local Url이 있다면 accept
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
        return

    def addPDF(self, links):
        #drag and drop을 통해 table_pdf에 pdf를 추가
        row_count = self.table_pdf.rowCount()
        for i, file in enumerate(links):
            filename = file.split('/')[-1]
            # 파일확장자가 pdf가 아니면 continue
            if filename.split('.')[-1] not in ['pdf','doc', 'docx', 'ppt', 'pptx', 'txt']:
                continue
            filepath = file.replace(filename, '')
            self.table_pdf.insertRow(row_count + i)
            self.table_pdf.setItem(row_count + i, 0, QTableWidgetItem(filename))
            self.table_pdf.setItem(row_count + i, 1, QTableWidgetItem(filepath))

        self.table_pdf.resizeColumnsToContents()
        return

    def deleteRow(self, event):
        # delete key가 눌리면 table_pdf에서 선택된 영역을 모두 지우도록 설정
        if event.key() == Qt.Key_Delete:
            for item in self.table_pdf.selectedItems():
                self.table_pdf.removeRow(item.row())

        return

    def set_pdfPath(self):
        #QFileDialog를 띄워 pdfpath를 설정
        pdfpath = QFileDialog.getExistingDirectory(self, 'pdfpath')
        self.line_pdfPath.setText(pdfpath)

        return

    def loadPDF(self):
        #pdfpath에 있는 pdf를 table_pdf에 출력
        pdfpath = self.line_pdfPath.text()
        files = []
        for ext in ('*.doc', '*.docx', '*.ppt', '*.pptx', '*.txt', '*.pdf'):
            files.extend(glob(join(pdfpath, ext)))

        #table_pdf 안에 있는 row의 개수 count
        row_count = self.table_pdf.rowCount()
        for i, file in enumerate(files):
            filename = file.split('\\')[-1]
            filepath = file.replace(filename, '')
            self.table_pdf.insertRow(row_count + i)
            self.table_pdf.setItem(row_count + i, 0, QTableWidgetItem(filename))
            self.table_pdf.setItem(row_count + i, 1, QTableWidgetItem(filepath))

        self.table_pdf.resizeColumnsToContents()

        return

    def buildDB(self):

        if self.table_pdf.rowCount() < 1:
            QMessageBox.about(self, '알림', 'PDF 파일을 추가하세요')
            return

        if self.checkSetting() == False:
            return

        self.text_DBStatus.setText('DB 생성 시작 ')
        QApplication.processEvents()

        #read items from table_pdf
        filelist = []
        for i in range(self.table_pdf.rowCount()):
            filename = self.table_pdf.item(i, 0).text()
            filepath = self.table_pdf.item(i, 1).text()
            filelist.append(f'{filepath}{filename}')

        self.docsearch = self.psv.setting(
            apiKey=self.line_key.text(),
            filelist=filelist,
            dbPath=self.dbPath,
            docSeparator='. ',
            docSize=self.slider_chunkSize.value(),
            docOverlap=self.slider_overlapSize.value(),
        )

        self.text_DBStatus.setText('DB 생성 완료 ')

        #DB 생성완료 메세지 출력
        QMessageBox.about(self, '알림', 'DB 생성 완료')

        return

    #필요한 설정값들이 모두 입력되어 있는지 확인하는 함수
    def checkSetting(self):
        #필요한 설정값들이 모두 입력되어 있는지 확인하는 함수
        if self.line_key.text() == '':
            QMessageBox.about(self, '경고', 'Open AI에서 발급받은 API Key를 입력하세요')
            return False

        #line_openaiM 값이 비어있으면 경고 메세지 출력
        if self.line_openaiM.text() == '':
            QMessageBox.about(self, '경고', 'Open AI Model을 입력하세요')
            return False

        return True

    '''#####################################
            설정 Frame 생성 함수 목록
       #####################################'''
    # 설정 Frame 생성 함수 목록
    def setup_fr_Setting(self):

        #help_key tooltip 작성
        self.help_key.setToolTip(
            '''OpenAi에서 발급받은 API Key를 입력하세요.\nhttps://platform.openai.com/account/api-keys 에서 확인하실 수 있습니다.'''
        )

        #help_openaiM tooltip 작성
        self.help_openaiM.setToolTip(
            '''OpenAI에서 호출할 GPT 모델명을 입력하세요.'''
        )

        #slider_evid와 line_evid의 값 연동
        self.slider_evid.valueChanged.connect(
            lambda: self.line_evid.setText(str(self.slider_evid.value()))
        )
        self.line_evid.textChanged.connect(
            lambda: self.slider_evid.setValue(int(self.line_evid.text()))
        )
        #help_numEvid tooltip 작성
        self.help_numEvid.setToolTip(
            '''컨센서스를 생성할 때 사용한 세부문서의 개수를 선택하세요.'''
        )

        #slider_calc와 line_calc의 값 연동
        self.slider_calc.valueChanged.connect(
            lambda: self.line_calc.setText(str(self.slider_calc.value()))
        )
        self.line_calc.textChanged.connect(
            lambda: self.slider_calc.setValue(int(self.line_calc.text()))
        )
        #help_numCalc tooltip 작성
        self.help_numCalc.setToolTip(
            '''OpenAI API를 한번 호출할 때, 처리할 근거의 개수를 입력하세요.\n토큰의 개수 제한으로 5개 이하가 추천됩니다.\n총 근거의 개수를 나눠서 0으로 만드는 것이 좋습니다.'''
        )

        #dial_evid와 line_evidF의 값 연동
        self.dial_evid.valueChanged.connect(
            lambda: self.line_evidF.setText(str(self.dial_evid.value()))
        )
        self.line_evidF.textChanged.connect(
            lambda: self.dial_evid.setValue(int(self.line_evidF.text()))
        )
        #help_evidF tooltip 작성
        self.help_evidF.setToolTip(
            '''1차적으로 근거를 요약할 때, 부여할 자유도를 지정합니다.\n자유도가 높을수록 AI가 근거에 추가적인 의견을 붙일 가능성이 높아집니다.'''
        )

        #dial_filter와 line_filterF의 값 연동
        self.dial_filter.valueChanged.connect(
            lambda: self.line_filterF.setText(str(self.dial_filter.value()))
        )
        self.line_filterF.textChanged.connect(
            lambda: self.dial_filter.setValue(int(self.line_filterF.text()))
        )
        #help_filterF tooltip 작성
        self.help_filterF.setToolTip(
            '''2차적으로 근거를 필터링할 때, 부여할 자유도를 지정합니다.\n자유도가 높을수록 AI가 근거에 추가적인 의견을 붙일 가능성이 높아집니다.'''
        )

        #dial_conc와 line_concF의 값 연동
        self.dial_conc.valueChanged.connect(
            lambda: self.line_concF.setText(str(self.dial_conc.value()))
        )
        self.line_concF.textChanged.connect(
            lambda: self.dial_conc.setValue(int(self.line_concF.text()))
        )
        #help_concF tooltip 작성
        self.help_concF.setToolTip(
            '''마지막으로 결론을 출력할 때, 부여할 자유도를 지정합니다.\n자유도가 높을수록 AI가 추가적인 의견을 붙일 가능성이 높아집니다.'''
        )

        #Consensus Generator 클래스 선언
        self.psv = PrintAssetView(
            llmAiEngine=self.line_openaiM.text(),
            temperature=float(self.dial_evid.value()/100),
            temperature_s=float(self.dial_filter.value()/100),
            temperature_agg=float(self.dial_conc.value()/100),
        )