import os
import shutil
import uuid
import smtplib

# from src.database import mydb

FILTER_COLS = ["course_id","name","disc_name","description","ins_name","logo","deg_name","level_type","curr_type","curr_value","intake_month","deadline_month","address","language", "dur_year"]
filters = [
    {
        "filter_name": "Country",
        "querry": "SELECT DISTINCT coun_name FROM country ORDER BY coun_name;",
        "type": "distinct",
        # "table_place": "country.coun_name",
        "table_place": "country",
    },
    {
        "filter_name": "Duration (years)",
        "querry": "SELECT MIN(dur_year), MAX(dur_year) FROM course_duration;",
        "type": "continuous",
        # "table_place": "course_duration.dur_year",
        "table_place": "dur",
    },
    {
        "filter_name": "Degree Level",
        "querry": "SELECT DISTINCT deg_name FROM degree_level ORDER BY deg_name;",
        "type": "distinct",
        # "table_place": "degree_level.deg_name",
        "table_place": "deg",
    },
    {
        "filter_name": "Discipline",
        "querry": "SELECT DISTINCT disc_name FROM discipline ORDER BY disc_name;",
        "type": "distinct",
        # "table_place": "discipline.disc_name",
        "table_place": "disc",
    },
    {
        "filter_name": "Fee",
        "querry": "SELECT MIN(pkr_value), MAX(pkr_value) FROM fee;",
        "type": "continuous",
        # "table_place": "fee.pkr_value",
        "table_place": "fee",
    },
    {
        "filter_name": "Institute",
        "querry": "SELECT DISTINCT ins_type FROM institute ORDER BY ins_type;",
        "type": "distinct",
        # "table_place": "institute.ins_type",
        "table_place": "ins",
    },
    {
        "filter_name": "Language",
        "querry": "SELECT DISTINCT language FROM language ORDER BY language;",
        "type": "distinct",
        # "table_place": "language.language",
        "table_place": "lang",
    },
]


def get_filter_options(cursor):
    results = []

    for filter in filters:
        cursor.execute(filter["querry"])

        result = {
            "filter_name": filter["filter_name"],
            "type": filter["type"],
        }

        if filter["type"] == "distinct":
            # old method
            # result['options'] = ["All"] + [i[0] for i in list(cursor)]

            opts = ["All"] + [i[0] for i in list(cursor)]
            new_ops = []
            for i, j in enumerate(opts):
                new_ops.append({"value": i + 1, "label": j})
            result["options"] = new_ops
        else:
            ran = list(cursor)
            result["options"] = [float(ran[0][0]), float(ran[0][1])]

        results.append(result)
    return results


def clean_word(word):
    alpha = "abcdefghijklmnopqrstuvwxyz"
    new = ""
    for i in word.lower():
        if i in alpha:
            new += i
    return new


def compare_word(word1, word2):
    word1_subs = [
        word1[i:j] for i in range(len(word1)) for j in range(i + 1, len(word1) + 1)
    ]
    word1_subs = sorted(word1_subs, key=lambda x: len(x), reverse=True)
    word1_subs = [i for i in word1_subs if len(i) > 2]

    score = 0
    for i in word1_subs:
        if i in word2:
            score += 1

    return score


def sort_by_search(search, results):
    cleaned_search = clean_word(search)

    new_results = []
    for result in results:
        score = compare_word(cleaned_search, clean_word(result[1]))
        new_results.append([result[0], score])
    sorted_ids = [i[0] for i in sorted(new_results, key=lambda x: x[1], reverse=True)]

    return sorted_ids


# Huzaifa start
def get_client_data_all(cursor, client_id):
    dict = {}
    sql = "select * from clients_crm where phnum =%s"
    cursor.execute(sql, [client_id])
    result = cursor.fetchall()
    dict["name"] = result[0][1]
    dict["phone"] = result[0][2]
    dict["email"] = result[0][3]
    dict["address"] = result[0][4]
    return dict


def get_full_convo(cursor, id):
    dict = {}
    sql = "select message,time,sender from convo where phnum=%s "
    cursor.execute(sql, [id])
    result = cursor.fetchall()
    dict["message"] = result
    return dict


def send_sms(cursor, body):
    value = (body["client_id"], body["message"], body["sender_name"])
    sql = "INSERT INTO convo (phnum,message,sender) VALUES (%s,%s,%s)"
    cursor.execute(sql, value)
    # mydb.commit()
    if cursor:
        return "ok"
    else:
        return 0


def get_clients_info(cursor):
    dict = {}
    sql = "select phnum,name from clients_crm"
    cursor.execute(sql)
    result = cursor.fetchall()
    dict["clients"] = result

    return dict


def create_new_client(cursor, body):
    value = (body["name"], body["phone"], body["email"], body["address"])
    sql = "INSERT INTO clients_crm (name,phnum,email,address) VALUES (%s,%s,%s,%s)"
    cursor.execute(sql, value)
    # mydb.commit()
    parentDir = "Images/ClientsData/"
    path = os.path.join(parentDir, body["phone"])
    os.mkdir(path)
    return "ok"


def get_crm_auth(cursor, body):
    dict = {}
    values = (body["Email"],)
    password = body["Password"]

    sql = "SELECT * FROM crm_users where email=%s"
    cursor.execute(sql, values)
    result = cursor.fetchall()
    if result == []:
        dict["status"] = "bad"
        dict["details"] = "user not found"
    elif result[0][3] == password:
        dict["status"] = "ok"
        dict["details"] = "user found"
        dict["name"] = result[0][1]
        dict["usertype"] = result[0][4]
    else:
        dict["status"] = "bad"
        dict["details"] = "wrong password"
    return dict


def delete_client(cursor, id):
    dir_path = "ClientsData/%s" % id
    shutil.rmtree(dir_path, ignore_errors=True)
    sql = "DELETE FROM clients_crm WHERE (phnum = %s)"
    cursor.execute(sql, [id])
    # mydb.commit()
    sql = "DELETE FROM convo WHERE phnum=%s"
    cursor.execute(sql, [id])
    # mydb.commit()
    print(cursor.fetchall())
    return {"status": "ok"}


def update_password(cursor, body):
   
    value = (body["pswd"], body["email"])
    sql = "Select password FROM crm_users WHERE (email=%s)"
    cursor.execute(sql, [value[1]])
    result = cursor.fetchall()
    if result:
        if result[0][0].__eq__(body["old"]) :
            sql = "UPDATE crm_users SET `password` = %s WHERE (`email` = %s)"
            cursor.execute(sql, value)
             # mydb.commit()
            return {"status": "ok"}
        else:
            return {"status": "WrongPassword"}
    else:
        return {"status": "Bad"}
        
    

    


def get_all_blogs(cursor):
    sql = "SELECT * FROM yec_blogs"
    cursor.execute(sql)
    result = cursor.fetchall()
    return result


def new_blog_post(cursor, body, img):
    id = uuid.uuid1()
    hex = str(id.hex)
    imgdir = "Images/Blogs/" + hex + ".jpg"
    sql = "insert into yec_blogs (title,dics,cover,category) VALUES (%s,%s,%s,%s) "
    value = (
        body["title"],
        body["decs"],
        imgdir,
        body["cat"],
    )
    cursor.execute(sql, value)
    # mydb.commit()
    with open(imgdir, "wb") as image:
        image.write(img.file.read())
        image.close()
    return {"status": "ok"}


def new_crm_user(cursor, body):
    value = (body["name"], body["email"], body["password"], body["usertype"])
    sql = "INSERT INTO crm_users (`name`, `email`, `password`, `user_type`) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, value)
    # mydb.commit()
    return [{"status": "ok"},{"Type", body["usertype"]}]

# ======== new ======== 

def upload_user_docs(phone_no, **kwargs):
    imgdir = f"Images/ClientsData/{phone_no}"

    # creating folder if it doesnot exist before
    if not os.path.exists(imgdir):
        os.mkdir(imgdir)
        
    for name, file in kwargs.items():
        if file:
            file_extension = file.filename.split(".")[-1]
            saving_filename = f"{imgdir}/{name}.{file_extension}"
            with open(saving_filename, 'wb') as f:
                f.write(file.file.read())
    
    return "ok"

def delete_user_docs(phone_no, delete):
    imgdir = f"Images/ClientsData/{phone_no}/"
    for file in os.listdir(imgdir):
        if file.split(".")[0] in delete:
            os.remove(imgdir + file)

    return "ok"

def news_letter_sub(mycursor, body):
    value =(body["name"],body["email"],body["phone"])
    sql ="INSERT INTO web_subs (`name`, `email`, `phone`) VALUES ( %s, %s, %s)"
    mycursor.execute(sql, value)
    result=mycursor.fetchall()
    if result:
        return {"status": "ok"}
    else:
        return {"status": "bad"}

def send_mails(mycursor, body):
    value =(body["name"],body["student"],body["worker"],body["immigrants"])
    sql ="INSERT INTO send_mails (`name`, `student`, `worker`, `immigrants`) VALUES ( %s, %s, %s, %s)"
    mycursor.execute(sql, value)
    return {"status": "ok"}
   

# huzaifa end


def get_full_info(cursor, course_id):
    dict = {}
    sql = "select spec_name from complete_data where course_id=%s "

    cursor.execute(sql, [course_id])
    result = cursor.fetchall()
    if result:        
        dict["specialization"] = result[0][0]
        sql = """select disc_name,description from complete_data where course_id=%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["discipline"] = result[0]
        sql = """select language from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["language"] = result[0][0]
        sql = """select `rank`,rank_type from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["ranking"] = result
        sql = """select ins_name,est_date,sector,ins_type,sector,logo from 
        complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["institute"] = result[0]
        sql = """select camp_name from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["campus"] = result[0][0]
        sql = """select city_name from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["city"] = result[0][0]
        sql = """select state_name from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["state"] = result[0][0]
        sql = """select coun_name from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["country"] = result[0][0]
        sql = """select deg_name,level_type from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["degree_level"] = result[0]
        sql = """select pkr_value from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["fee_in_pkr"] = result[0][0]
        sql = """select intake_month from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["intake_months"] = result
        sql = """select deadline_month from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["deadline_month"] = result
        sql = """select deadline_year from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["deadline_year"] = result
        sql = """select curr_type,curr_value from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["currency_value"] = result[0]
        sql = """select type,url from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["source_link"] = result[0]
        sql = """select name from complete_data where course_id =%s """

        cursor.execute(sql, [course_id])
        result = cursor.fetchall()
        dict["course"] = result[0]
        return dict
    else:
       return("not found")
        


def get_short_info(cursor, course_ids):

    sql = f"""
        SELECT
            {",".join(FILTER_COLS)}
        FROM
            complete_data
        WHERE
            {" OR ".join([f"course_id = {i}" for i in course_ids])}
        ;
    """

    cursor.execute(sql)
    data = cursor.fetchall()

    results = {}
    for row in data:
        if row[0] not in results.keys():
            results[row[0]] = {}
        for i, col in enumerate(FILTER_COLS[1:]):
            results[row[0]][col] = list(set(results[row[0]].get(col, []) + [row[i+1]]))

    for key in results.keys():
        results[key]['course_id'] = key

    return list(results.values())

def apply_filter(cursor, body):
    def get_distinct_query(key, val):
        if val == ["All"]:
            return " ( true ) "

        table_place = [
            filter["table_place"] for filter in filters if filter["filter_name"] == key
        ][0]
        q = "("
        for v in val:
            q += f' {table_place} = "{v}" OR'
        q = q[:-3] + ")"

        return q

    def get_cont_query(key, val):
        table_place = [
            filter["table_place"] for filter in filters if filter["filter_name"] == key
        ][0]
        return f" ( {table_place} >= {val[0]} AND {table_place} <= {val[1]} ) "

    def fill_condition(where_clause="true"):
        return f"""
			SELECT
				course_id
			FROM
				filters_data
			WHERE
				{where_clause}
                AND
                REPLACE(LOWER(name), " ", "") LIKE "%{body.get("search", "").lower().replace(" ", "")}%"
            LIMIT {body.get("start", 0)},{body.get("end", 30)}
			
		"""

    query = ""
    for filter in filters:
        if filter["type"] == "distinct":
            query += (
                get_distinct_query(
                    filter["filter_name"], body.get(filter["filter_name"], ["All"])
                )
                + " AND "
            )
        else:
            query += (
                get_cont_query(
                    filter["filter_name"], body.get(filter["filter_name"], [0, 1e20])
                )
                + " AND "
            )
    query = query[:-4]

    sub_query = fill_condition(
        where_clause = query,
    )

    cursor.execute(sub_query)
    results = cursor.fetchall()
    course_ids = [i[0] for i in results]

    return get_short_info(cursor, course_ids)

"""
{
	"search": "",
	"limit": 100,

	"Country": ["All"],
	"Duration (years)": [2, 3],
	"Degree Level": ["Bachelors","Certificate","Diploma"],
	"Discipline": ["All"],
	"Fee": [1203255.96, 13068627.27],
	"Institute": ["University"],
	"Language": ["All"],
}
"""
def visit_visa(mycursor, body):
    value =(body["firstname"],body["lastname"],body["email"],body["number"],body["countryinterest"],body["timevisit"],body["details"],body["meet"])
    sql ="INSERT INTO visit_visa (`firstname`,`lastname`, `email`, `number`, `countryinterest`, `timevisit`, `details`, `onlinemeet`) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s)"
    mycursor.execute(sql, value)
    return {"status": "ok"}

def immigration_visa(mycursor, body):
    value =(body["firstname"],body["lastname"],body["email"],body["number"],body["details"],body["meet"])
    sql ="INSERT INTO immigration_visa (`firstname`,`lastname`, `email`, `number`, `details`, `onlinemeet`) VALUES ( %s, %s, %s, %s, %s, %s)"
    mycursor.execute(sql, value)
    return {"status": "ok"}
def student_visa(mycursor, body):
    value =(body["firstname"],body["lastname"],body["email"],body["number"],body["ielts"],body["reading"],body["writing"],body["listning"],body["speaking"],body["details"],body["meet"])
    sql ="INSERT INTO student_visa (`firstname`,`lastname`, `email`, `number`, `ielts`, `reading`, `writing`, `listning`, `speaking`, `details`, `onlinemeet`) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    mycursor.execute(sql, value)
    return {"status": "ok"}
def work_visa(mycursor, body):
    value =(body["firstname"],body["lastname"],body["email"],body["number"],body["pastexperience"],body["company"],body["jobtitle"],body["specialization"],body["details"],body["meet"])
    sql ="INSERT INTO work_visa (`firstname`,`lastname`, `email`, `number`, `pastexperience`, `company`, `jobtitle`, `specialization`, `details`, `onlinemeet`) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    mycursor.execute(sql, value)
    return {"status": "ok"}
def TestMail(mycursor,body):
     value =body["name"],body["email"]
    # change these as per use
     your_email = "huzaifatawab@youreduconnect.com"
     your_password = "huz12345"
    # establishing connection 
     server = smtplib.SMTP_SSL('mail.youreduconnect.com', 465)
     server.ehlo()
     server.login(your_email, your_password)
    # getting the names and the emails
     emails = body["email"]
    # iterate through the records
     for i in range(len(emails)):
    # for every record get the name and the email addresses
       email = emails[i]
       print(email)
    # the message to be emailed
       message = "Hello"
    # sending the email
       server.sendmail(your_email, [email], message)
    # close the smtp server
     server.close()
     return (value)