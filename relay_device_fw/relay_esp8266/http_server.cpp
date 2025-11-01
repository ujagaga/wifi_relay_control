/* 
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *  
 *  HTTP server which generates the web browser pages. 
 */
 
#include <ESP8266WebServer.h>
#include <pgmspace.h>
#include "wifi_connection.h"
#include "config.h"
#include "relay_esp8266.h"
#include "pinctrl.h"


/* If we were writing HTML files, this would be the content. Here we use char arrays. */
static const char HTML_BEGIN[] PROGMEM = R"(
<!DOCTYPE HTML>
<html>
  <head>
    <meta name = "viewport" content = "width = device-width, initial-scale = 1.0, maximum-scale = 1.0, user-scalable=0">
    <title>Zaric Gate</title>
    <style>
      body { background-color: white; font-family: Arial, Helvetica, Sans-Serif; Color: #000000; }
      .contain{width: 100%;}
      .center_div{margin:0 auto; max-width: 400px;position:relative;}
    </style>
  </head>
  <body>
)";

static const char HTML_END[] PROGMEM = "</body></html>";

static const char INDEX_HTML_0[] PROGMEM = R"(
<style>
  .btn_b{border:0;border-radius:0.3rem;color:#fff;line-height:4rem;font-size:3rem;margin:1%;height:4rem;width:4rem;background-color:#1fa3ec;flex:1;}
  .btn_cfg{border:0;border-radius:0.3rem;color:#fff;line-height:1.4rem;font-size:0.8rem;margin:1ch;height:2rem;width:10rem;background-color:#ff3300;}      
  .row{display: flex;justify-content: space-between;align-items: center;}      
</style>
<div class="contain">
  <div class="center_div">
)";

const char INDEX_HTML_1[] PROGMEM = R"(
  </div>
  <hr>
  <p id='status'></p>  
  <br>
  <button class="btn_cfg" type="button" onclick="location.href='/selectap';">Configure wifi</button>
  <br/>
</div>
<script>
  function redirectTo(id) {
    const timestamp = new Date().getTime();
    location.href = `/trigger?id=${id}&t=${timestamp}`;
  }
</script>
)";

static const char APLIST_HTML_0[] PROGMEM = R"(
<style>
  .c{text-align: center;}
  div,input{padding:5px;font-size:1em;}
  input{width:95%;}
  body{text-align: left;}
  button{width:100%;border:0;border-radius:0.3rem;color:#fff;line-height:2.4rem;font-size:1.2rem;height:40px;background-color:#1fa3ec;}
  .q{float: right;width: 64px;text-align: right;}
  .radio{width:2em;}
  #vm{width:100%;height:50vh;overflow-y:auto;margin-bottom:1em;} 
</style>
</head><body>  
  <div class="contain">
    <div class="center_div">
)";    

/* Placeholder for the wifi list */
static const char APLIST_HTML_1[] PROGMEM = R"(   
      <h1 id='ttl'>Networks found:</h1>
      <div id='vm'>
)";  

static const char APLIST_HTML_2[] PROGMEM = R"( 
      </div>
      <form method='get' action='wifisave'>
        <button type='button' onclick='refresh();'>Rescan</button><br/><br/>
        <input id='s' name='s' length=32 placeholder='SSID (Leave blank for AP mode)'><br>      
        <input id='p' name='p' length=32 placeholder='password'><br>        
        <br><button type='submit'>save</button>        
      </form>      
     </div>
  </div>
<script>
  function c(l){
    document.getElementById('s').value=l.innerText||l.textContent;
    document.getElementById('p').focus();
  }
  
  var cn=new WebSocket('ws://'+location.hostname+':81/');
  cn.onopen=function(){
    cn.send('{"APLIST":""}');
  }
  cn.onmessage=function(e){
    var data=JSON.parse(e.data);
    if(data.hasOwnProperty('APLIST')){
      rsp=data.APLIST.split('|');
      document.getElementById('vm').innerHTML='';
      for(var i=0;i<(rsp.length);i++){
        document.getElementById('vm').innerHTML+='<span>'+(i+1)+": </span><a href='#p' onclick='c(this)'>" + rsp[i] + '</a><br>';
      }
      if(!document.getElementById('vm').innerHTML.replace(/\\s/g,'').length){
        document.getElementById('ttl').innerHTML='No networks found.'
      } 
    }
  };
  function refresh(){
    document.getElementById('vm').innerHTML='Please wait...'
    cn.send('{"APLIST":""}');
  } 
</script>
)";

static const char REDIRECT_HTML[] PROGMEM = R"(
<p id="tmr"></p>
<script>
  var c=6;   
  function count(){
    var tmr=document.getElementById('tmr');   
    if(c>0){
      c--;
      tmr.innerHTML="You will be redirected to home page in "+c+" seconds.";
      setTimeout('count()',1000);
    }else{
      window.location.href="/";
    }
  }
  count();
</script> 
)";

static const char OTA_HTML[] PROGMEM = R"(
<html><head> <title>OTA Update</title></head>
<body>
  <h1>OTA Update</h1>
  <p>Starting the update server.</p>
  <p>If no update starts in 5 minutes, will stop the update server and restore default functionallity.</p>
</body>
</html>
)";

/* Declaring a web server object. */
ESP8266WebServer* webServer = nullptr;

void showStartPage() { 
  String response = FPSTR(HTML_BEGIN);
  response += FPSTR(INDEX_HTML_0);
  response += "<div class='row'>";
  response += "<button class=\"btn_b\" type=\"button\" onclick=\"redirectTo(0)\"><</button>";
  response += "<button class=\"btn_b\" type=\"button\" onclick=\"redirectTo(1)\">></button>";  
  response += "<button class=\"btn_b\" type=\"button\" onclick=\"redirectTo(2)\">&frac12;</button>";  
  response += "<button class=\"btn_b\" type=\"button\" onclick=\"redirectTo(3)\">x</button>"; 
  response += "</div>";

  response += FPSTR(INDEX_HTML_1); 
  response += FPSTR(HTML_END);
  webServer->send(200, "text/html", response);  
}

static void trigger(void){
  if (webServer->hasArg("id")) {
    String idStr = webServer->arg("id");
    int id = idStr.toInt();

    PINCTRL_trigger(id);    
  }
  showStartPage();  
}

static void showNotFound(void){
  webServer->send(404, "text/html; charset=iso-8859-1","<html><head> <title>404 Not Found</title></head><body><h1>Not Found</h1></body></html>"); 
}

static void showStatusPage(bool goToHome = false) {    
  Serial.println("showStatusPage");
  String response = FPSTR(HTML_BEGIN);
  response += "<h1>Connection Status</h1><p>";
  response += MAIN_getStatusMsg() + "</p>";
  if(goToHome){
    /* Add redirect timer. */
    response += FPSTR(REDIRECT_HTML);
  }
  response += FPSTR(HTML_END);
  webServer->send(200, "text/html", response);   
}


static void showRedirectPage(void){  
  showNotFound();
}

static void selectAP(void) {   
  Serial.println("selectAP");
  String response = FPSTR(HTML_BEGIN);
  response += FPSTR(APLIST_HTML_0);  
  response += FPSTR(APLIST_HTML_1);
  response += "Please wait...";  
  response += FPSTR(APLIST_HTML_2);   
  response += FPSTR(HTML_END);
  webServer->send(200, "text/html", response);  
}

static void saveWiFi(void){
  String ssid = webServer->arg("s");
  String pass = webServer->arg("p");
  
  if((ssid.length() > 63) || (pass.length() > 63)){
      MAIN_setStatusMsg("Sorry, this module can only remember SSID and a PASSWORD up to 63 bytes long.");
      showRedirectPage(); 
      return;
  } 

  String st_ssid = WIFIC_getStSSID();
  String st_pass = WIFIC_getStPass();

  if(st_ssid.equals(ssid) && st_pass.equals(pass)){
      MAIN_setStatusMsg("All parameters are already set as requested.");
      showRedirectPage();      
      return;
  }   

  WIFIC_setStSSID(ssid);
  WIFIC_setStPass(pass);

  String http_statusMessage;

  if(ssid.length() > 3){    
    http_statusMessage = "Saving settings and connecting to SSID: ";
    http_statusMessage += ssid;    
  }else{       
    http_statusMessage = "Saving settings and switching to AP mode only.";    
  }
  http_statusMessage += "<br>If you can not connect to this device 20 seconds from now, please, reset it.";

  MAIN_setStatusMsg(http_statusMessage);
  showStatusPage();

  volatile int i;

  /* Keep serving http to display the status page*/
  for(i = 0; i < 100000; i++){
    webServer->handleClient(); 
    ESP.wdtFeed();
  } 

  /* WiFI config changed. Restart to apply. 
   Note: ESP.restart is buggy after programming the chip. 
   Just reset once after programming to get stable results. */

  ESP.restart();
}

void HTTP_SERVER_process(void){
  webServer->handleClient(); 
}

void HTTP_SERVER_init(void){   
  if (webServer != nullptr) {
    delete webServer; // Clean up old one
  }
  webServer = new ESP8266WebServer(80);

  webServer->on("/", showStartPage);
  webServer->on("/favicon.ico", showNotFound);
  webServer->on("/selectap", selectAP);
  webServer->on("/trigger", trigger);
  webServer->on("/wifisave", saveWiFi);
  // webServer->on("/update", startOtaUpdate);  
  webServer->onNotFound(showStartPage);
  
  webServer->begin();
}
