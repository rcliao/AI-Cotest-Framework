package antServer.servlet;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintWriter;

import java.io.InputStream;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.MultipartConfig;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.tomcat.util.http.fileupload.FileItem;
import org.apache.tomcat.util.http.fileupload.FileUploadException;
import org.apache.tomcat.util.http.fileupload.disk.DiskFileItemFactory;
import org.apache.tomcat.util.http.fileupload.servlet.ServletFileUpload;
import org.apache.commons.io.*;

import java.lang.ProcessBuilder;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.List;

import antServer.servlet.User;

/**
 * Servlet implementation class AntServer
 */
//@WebServlet("/AntServer")
@WebServlet(urlPatterns = "/AntServer/*", loadOnStartup = 2)
public class AntServer extends HttpServlet {
	private static final long serialVersionUID = 1L;
	
	ServerSpecifications serverSpecs = new ServerSpecifications();
	ServerData serverData = new ServerData();
	
	public boolean addBotCMD(String FileName, String BotName, String Password) throws ServletException, IOException{
		
		PrintWriter out = new PrintWriter(new FileWriter(serverSpecs.getBotsFolderPath()+"tmpcmd.cmd"));
		out.print("start " + serverSpecs.getPythonPath() + " " +  
				serverSpecs.getTcpClientPath() + " " +
				"localhost " + serverSpecs.getPortNumberString() + " " + 
				serverSpecs.getBotsFolderPath().concat(FileName) + " " + 
				BotName +
				" " +
				Password);
		
		out.close();
		
		ProcessBuilder pb = new ProcessBuilder(serverSpecs.getBotsFolderPath()+"uk.cmd");
		//ProcessBuilder pb = new ProcessBuilder(serverSpecs.getBotsFolderPath()+"tmpcmd.cmd");

        try 
        {
            pb.start();
            System.out.println("cmd started");
        } 
        catch (IOException e) 
        {
            System.out.println(e.getMessage());
        }

		
		return true;
	}
	
	public boolean addBot(String FileName, String BotName, String Password) throws ServletException, IOException{
		
		//addBotCMD(FileName, BotName, Password);
		//return true;
		
		/*String cmd[] = new String[11];
		//if (FileName.substring(FileName.lastIndexOf('.') + 1) == "exe")
		//{
			//String cmd[] = new String[11];
			//cmd = new String[11];
			cmd[0] = "cmd";
			cmd[1] = "/k";
			cmd[2] = "start";
			cmd[3] = serverSpecs.getPythonPath();
			cmd[4] = serverSpecs.getTcpClientPath();
			cmd[5] = "localhost";
			cmd[6] = serverSpecs.getPortNumberString();
			cmd[7] = serverSpecs.getBotsFolderPath().concat(FileName); //"e:/MyFiles/Dropbox/!EDU/OLD/!!CS460/AntAI/ants-tcp-master/KondasBot6.exe";
			cmd[8] = BotName;
			cmd[9] = "password";
			cmd[10] = Password;
		//}
			*/
		
		
		String cmd[] = new String[12];
		if (FileName.substring(FileName.lastIndexOf('.') + 1).equalsIgnoreCase("exe"))
		{
			System.out.println("Recognized exe2");
			//String cmd[] = new String[11];
	        cmd[0] = "cmd";
	        cmd[1] = "/k";
	        cmd[2] = "start";
	        
	        cmd[3] = "cmd.exe";
	        cmd[4] = "/k";
	        
	        cmd[5] = serverSpecs.getPythonPath();
	        cmd[6] = serverSpecs.getTcpClientPath();
	        cmd[7] = "localhost";
	        cmd[8] = serverSpecs.getPortNumberString();
	        cmd[9] = serverSpecs.getBotsFolderPath().concat(FileName);
	        cmd[10] = BotName;
	        //cmd[11] = "password";
	        cmd[11] = Password;
	        Runtime rt = Runtime.getRuntime();
	        Process pr = rt.exec(cmd);
	        return true;
		}
		
		else if (FileName.substring(FileName.lastIndexOf('.') + 1).equalsIgnoreCase("jar"))
		{
			System.out.println("Recognized jar");
			cmd = new String[12];
	        cmd[0] = "cmd";
	        //cmd[1] = "/k";
	        cmd[1] = "/k";
	        cmd[2] = "start";
	        cmd[3] = serverSpecs.getPythonPath();
	        cmd[4] = serverSpecs.getTcpClientPath();
	        cmd[5] = "localhost";
	        cmd[6] = serverSpecs.getPortNumberString();
	        cmd[7] = "\"java";
	        cmd[8] = "-jar";
	        cmd[9] = serverSpecs.getBotsFolderPath().concat(FileName).concat("\"");
	        cmd[10] = BotName;
	        //cmd[11] = "password";
	        cmd[11] = Password;
	        Runtime rt = Runtime.getRuntime();
	        Process pr = rt.exec(cmd);
	        return true;
		}
		for (int i = 0; i<cmd.length; i++)
		{
			System.out.println(cmd[i]);
		}
		return false;
			
		//Runtime rt = Runtime.getRuntime();
		//Process pr = rt.exec(cmd);
		
		
	}
	
    public AntServer() {
        super();
    }
    
    public void init( ServletConfig config ) throws ServletException
    {
        super.init( config );
        
        try
        {
            Class.forName( "com.mysql.jdbc.Driver" );
        }
        catch( ClassNotFoundException e )
        {
            throw new ServletException( e );
        }

        serverData.addUser(new User("jdoe", "1234"));
        serverData.addUser(new User("user2", "2345"));
		
		String serverStatus = "OFFLINE";
		if (getWebserverConnStatus())
				serverStatus = "ONLINE";
		
        getServletContext().setAttribute( "serverStatus", serverStatus );
        getServletContext().setAttribute("users", serverData.users);
        
      }
    
    public boolean getWebserverConnStatus(){
    	
    	int temp = 0;
    	try{
    	URL url = new URL("http://192.168.2.198:2080");
 		HttpURLConnection connection = (HttpURLConnection) url.openConnection();
 		connection.setRequestMethod("HEAD");
 		temp = connection.getResponseCode();
 		System.out.println(connection.getResponseCode());
 		connection.disconnect();
 		}
 		catch (IOException e)
 		{
 				
 		}
 		
 		if (temp == 200) return true;
 		else return false;
    }
    
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {

		String serverStatus = "OFFLINE";
		//if (getWebserverConnStatus())
				serverStatus = "ONLINE";
				
		String testExt = "hello.txt";
		testExt.substring(testExt.lastIndexOf('.') + 1);
		System.out.println(testExt);
		System.out.println(testExt.substring(testExt.lastIndexOf('.') + 1));
		
        getServletContext().setAttribute( "serverStatus", serverStatus );
		request.getRequestDispatcher("/WEB-INF/AntHome.jsp").forward(request, response);
		
	}


	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		try {
			String BotName = "";
			String Password = "";
	        List<FileItem> items = new ServletFileUpload(new DiskFileItemFactory()).parseRequest(request);
	        for (FileItem item : items) {
	        	
	            if (item.isFormField()) {
	                // Process regular form field (input type="text|radio|checkbox|etc", select, etc).
	                String fieldname = item.getFieldName();
	                System.out.println(fieldname);
	                if (fieldname.equals("botName")){
	                	String fieldvalue = item.getString();
	                	System.out.println(fieldvalue);
	                	if (!fieldvalue.equals(""))
	                		BotName = fieldvalue;
	                }
	                else if (fieldname.equals("password")){
	                	String fieldvalue = item.getString();
	                	System.out.println(fieldvalue);
	                	if (!fieldvalue.equals(""))
	                		Password = fieldvalue;
	                }
	                
	            } else {
	                // Process form file field (input type="file").
	                String fieldname = item.getFieldName();
	                System.out.println(fieldname);
	                String filename = FilenameUtils.getName(item.getName());
	                String filenameNoExt = filename.split("\\.")[0];
	                //String filename = "uploadedfile";
	                InputStream filecontent = item.getInputStream();
	                
	                
	                OutputStream out = null;
	                //final PrintWriter writer = response.getWriter();
	                out = new FileOutputStream(new File("c:\\tmp\\" + File.separator + filename));
	                int read = 0;
	                final byte[] bytes = new byte[1024];

	                while ((read = filecontent.read(bytes)) != -1) {
	                    out.write(bytes, 0, read);
	                }
	                if (out != null) {
	                    out.close();
	                }
	                if (filecontent != null) {
	                    filecontent.close();
	                }
	                //System.out.println("BotName: "+ BotName);
	                if (BotName.equals("")) BotName = filenameNoExt;
	                if (Password.equals("")) Password = "-1";
	                //if (addBot(filename,BotName,"-1"))
	                if (addBot(filename,BotName,Password))
	                {
	                	request.getRequestDispatcher("/WEB-INF/UploadSuccess.jsp").forward(request, response);
	                }
	                else
	                {
	                	request.getRequestDispatcher("/WEB-INF/UploadFailed.jsp").forward(request, response);
	                }
	                System.out.println("BotName: "+ BotName);
	            }
	            
	        }
	        //request.getRequestDispatcher("/WEB-INF/AntHome.jsp").forward(request, response);
	    } catch (FileUploadException e) {
	        throw new ServletException("Cannot parse multipart request.", e);
	    }
	}

}
