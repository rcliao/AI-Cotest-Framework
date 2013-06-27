<%@ page language="java" contentType="text/html; charset=ISO-8859-1"
    pageEncoding="ISO-8859-1"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %> 
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>CSULA AntAi Arena</title>
        <!--link rel="icon" href='/favicon.ico'-->
        <title>Hades</title>
        <style>
    a{
        text-decoration: none;
        color:#666;
    }
    a:hover{
        color:#aaa;
    }
    body {
        font-family:Calibri,Helvetica,Arial;
        font-size:9pt;
        color:#111;
    }
    hr {
        color:#111;
        background-color:#555;
    }
    table.tablesorter {
        background-color: #CDCDCD;
        font-family: Calibri,Helvetica,Arial;
        font-size: 8pt;
        margin: 10px 10px 15px 10px;
        text-align:left;
    }
    table.tablesorter thead tr th tfoot  {
        background-color:#E6EEEE;
        border:1px solid #FFFFFF;
        font-size:8pt;
        padding:4px 40px 4px 4px;
        background-position:right center;
        background-repeat:no-repeat;
        cursor:pointer;
    }
    table.tablesorter tbody td {
        background-color:#FFFFFF;
        color:#3D3D3D;
        padding:4px;
        vertical-align:top;
    }
    table.tablesorter tbody tr.odd td {
        background-color:#F0F0F6;
    }
    table.tablesorter thead tr .headerSortUp {
        background-color:#AAB;
    }
    table.tablesorter thead tr .headerSortDown {
        background-color:#BBC;
    }
</style>
                <script type="text/javascript" src="/js/jquery-1.2.6.min.js"></script>
                <script type="text/javascript" src="/js/jquery.tablesorter.min.js"></script>
                </head><body><b> &nbsp;&nbsp;&nbsp;
        <a href='/' name=top onclick="javascript:event.target.port=2080"> Games </a> &nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/ranking' onclick="javascript:event.target.port=2080"> Rankings </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/maps' onclick="javascript:event.target.port=2080"> Maps </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='http://antserver.ddns01.com:8080/AntServer/AntServer/ title='Upload your bot'> Upload Bot </a>
        <br><p></b>
</head>
<body>
Upload failed:
Only '.exe' and '.jar' extensions are supported currently.
</body>
</html>