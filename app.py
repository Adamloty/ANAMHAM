from telegram.ext import Application, CommandHandler, MessageHandler, filters
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_openai import OpenAIEmbeddings, OpenAI, ChatOpenAI
import asyncio
import mysql.connector

load_dotenv()

embeddings = OpenAIEmbeddings()

loader = UnstructuredExcelLoader("Book1.xlsx")
docs = loader.load()

filtered_docs = filter_complex_metadata(docs)

vecstore = Chroma.from_documents(filtered_docs, embeddings)

qa = RetrievalQA.from_chain_type(
    llm=OpenAI(temperature=0.2),
    chain_type="stuff",
    retriever=vecstore.as_retriever(),
)

TELEGRAM_TOKEN = "6690917212:AAG1YIpaxuqEUey0HkEk3BYHnkw-Bi351yM"

db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="rootadam",
    database="anamhamoud"
)

cursor = db.cursor(buffered=True)
cursor.execute("SELECT * FROM adm")
#cursor.execute("ALTER TABLE ada ADD COLUMN `id` INT AUTO_INCREMENT")
#cursor.execute("ALTER TABLE ada ADD PRIMARY KEY (`id`)")


async def start(update, context):
    await update.message.reply_text('انا محمود خدمة عملاء')

async def handle_message(update, context):
    user_message = update.message.text
    answer = qa.run(user_message)
    if not answer or 'مش فاهم السؤال انا حضرتك' in answer:
        answer = "ينفع توضح السؤال اكتر لو سمحت?"
    elif 'عايز احجز' in user_message and not context.user_data.get('booking'):
        context.user_data['booking'] = True
        answer = "اسمك ايه؟"
    elif 'خلاص مش عايز احجز' in user_message:
        context.user_data.clear()
        answer = "ماشي، لو احتجت أي مساعدة تانية قولي وأنا تحت أمرك."
    elif context.user_data.get('booking'):
        if 'name' not in context.user_data:
            context.user_data['name'] = user_message
            answer = "رقم تليفونك ايه؟"
        elif 'phone_number' not in context.user_data:
            context.user_data['phone_number'] = user_message
            answer = "تاريخ ميلادك ايه؟"
        elif 'birthdate' not in context.user_data:
            context.user_data['birthdate'] = user_message
            answer = "تختار قسم برمجة ولا جرافيك؟"
        elif 'department' not in context.user_data:
            context.user_data['department'] = user_message
            answer = "الكورس تحب يكون اونلاين ولا حضوري؟"
        elif 'course_type' not in context.user_data:
            context.user_data['course_type'] = user_message
            answer = "المواعيد تفضل يوم الحد ولا الاربع؟"
        elif 'day' not in context.user_data:
            context.user_data['day'] = user_message
            answer = "نوع الاشتراك: 1550 على خمس شهور ولا 444 على شهر؟"
        else:
            subscription_type = user_message
            # جمع كل البيانات من context.user_data
            name = context.user_data['name']
            phone_number = context.user_data['phone_number']
            birthdate = context.user_data['birthdate']
            department = context.user_data['department']
            course_type = context.user_data['course_type']
            day = context.user_data['day']
            # إدراج البيانات في الجدول
            cursor.execute("""
                INSERT INTO adm (`name`, `phone_number`, `data`, `proogr`, `city`, `an`, `price`) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, phone_number, birthdate, department, course_type, day, subscription_type))
            db.commit()
            answer = "تم تسجيل حجزك بنجاح، فريقنا هيتواصل معاك في أقرب وقت."
            context.user_data.clear()
            await update.message.reply_text(answer)
            cursor.execute("INSERT INTO ada (`name a`, `phone_number a`) VALUES (%s, %s)", (name, phone_number))

            db.commit()
            context.user_data.clear()  
    #await asyncio.sleep(2)
    await update.message.reply_text(answer)

application = Application.builder().token(TELEGRAM_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

application.run_polling()
