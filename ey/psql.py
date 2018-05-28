#/usr/bin/python

import psycopg2,psycopg2.extras,sys
pghost=''
pgport=str(5432)
dbuser=''
dbpasswd=''

def psqlCommand(database,command):

    connectstring="dbname="+database+" user="+dbuser+" password="+dbpasswd+" host="+pghost+" port="+str(pgport)

    try:
        p=psycopg2.connect(connectstring)
    except:
        err="Cannot connect to database"
        sys.stderr.write(err+"\n")
        sys.exit(1)

    cur = p.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(command)
    table=cur.fetchall()
    p.commit()
    p.close()
    return table
