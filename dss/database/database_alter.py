# import the module sqlite3

import sqlite3

 # Make a connection to the SQLite DB
dbCon = sqlite3.connect("dss/database/site.db")

# Obtain a Cursor object to execute SQL statements
cur   = dbCon.cursor()

# Add a new column to student table
addColumn = "ALTER TABLE TechnologyDB ADD COLUMN Homogeneitymax varchar(32)"

cur.execute(addColumn)

# Retrieve the SQL statment for the tables and check the schema

masterQuery = "select * from sqlite_master"

cur.execute(masterQuery)

tableList = cur.fetchall()

 

for table in tableList:

    print("Database Object Type: %s"%(table[0]))

    print("Database Object Name: %s"%(table[1]))

    print("Table Name: %s"%(table[2]))

    print("Root page: %s"%(table[3]))

    print("**SQL Statement**: %s"%(table[4]))

 

# close the database connection

dbCon.close()