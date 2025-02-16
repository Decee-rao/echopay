#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 21  // RFID SDA pin (GPIO5)
#define RST_PIN 22 // RFID RST pin (GPIO22)

// WiFi Credentials
const char* ssid = "Hotspot AKS";
const char* pass = "patanahi";
bool balanceCheckFlag = false;
int resp = 0;

// Server Config
String serverIP = "http://<ESP_IP>"; // Replace with actual server IP

AsyncWebServer server(80);
MFRC522 mfrc522(SS_PIN, RST_PIN);   // Create MFRC522 instance.
MFRC522::MIFARE_Key key;

String cardUID = "No card detected"; 
String espid = "1010"; 
int Tamount = 0;

void setup() {
    Serial.begin(115200);
    SPI.begin(18, 19, 23); // SPI Pins (SCK, MISO, MOSI)
    mfrc522.PCD_Init();    

    // Connect to WiFi
    WiFi.begin(ssid, pass);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected to WiFi");
    Serial.println(WiFi.localIP());

    // Web Server to display JSON response
    server.on("/uid", HTTP_GET, [](AsyncWebServerRequest *request) {
        String jsonResponse = "{\"uid\": \"" + cardUID + "\" , \"espid\": \"" + espid + "\"}";
        request->send(200, "application/json", jsonResponse);
    });

    server.on("/call", HTTP_GET, [](AsyncWebServerRequest *request) {
        String jsonResponse = "{\"flag\": \"" + String(resp) + "\" }";
        request->send(200, "application/json", jsonResponse);
    });

    // Endpoint to extract response parameter
    server.on("/1010", HTTP_GET, [](AsyncWebServerRequest *request) {
        if (request->hasParam("response")) {  
            String responseValue = request->getParam("response")->value();
            Serial.println("Received response parameter: " + responseValue);
            Tamount = responseValue.toInt();
        }
        String jsonResponse = "{\"espid\": \"1010\"}";
        request->send(200, "application/json", jsonResponse);
    });

    for (byte i = 0; i < 6; i++) {
        key.keyByte[i] = 0xFF;
    }

    Serial.println(F("Scan a MIFARE Classic PICC to read and update balance."));
    server.begin();
}

void loop() {
    if (!mfrc522.PICC_IsNewCardPresent()) return;
    if (!mfrc522.PICC_ReadCardSerial()) return;

    balanceCheckFlag = false;

    // while (Tamount == 0) {
    //     Serial.println("Waiting for Tamount...");
    //     delay(100);
    // }

    // Read and store UID
    cardUID = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
        cardUID += String(mfrc522.uid.uidByte[i], HEX);
    }
    Serial.println("Card UID: " + cardUID);
    Serial.println(Tamount);

    dump_byte_array(mfrc522.uid.uidByte, mfrc522.uid.size);
    Serial.println();

    byte blockAddr = 4;
    byte trailerBlock = 7;
    MFRC522::StatusCode status;
    byte buffer[18];
    byte size = sizeof(buffer);

    // Authenticate using key A
    Serial.println(F("Authenticating using key A..."));
    status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock, &key, &(mfrc522.uid));
    if (status != MFRC522::STATUS_OK) {
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
    }

    // Read balance
    Serial.print(F("Reading balance from block "));
    Serial.println(blockAddr);
    status = mfrc522.MIFARE_Read(blockAddr, buffer, &size);
    if (status != MFRC522::STATUS_OK) {
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
    }

    int balance = atoi((char*)buffer);
    Serial.print(F("Current balance: "));
    Serial.println(balance);

    // Update balance
    int newBalance = balance + Tamount;
    char moneyData[16];
    snprintf(moneyData, sizeof(moneyData), "%d", newBalance);

    if (balance == 0) {
        balanceCheckFlag = true;
    }
    if (balanceCheckFlag) {
        resp = 1;
    }

    // Write updated balance
    Serial.print(F("Writing new balance: "));
    Serial.println(newBalance);
    status = mfrc522.MIFARE_Write(blockAddr, (byte*)moneyData, 16);
    if (status != MFRC522::STATUS_OK) {
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
    }

    // Read new balance for verification
    status = mfrc522.MIFARE_Read(blockAddr, buffer, &size);
    if (status != MFRC522::STATUS_OK) {
        Serial.println(mfrc522.GetStatusCodeName(status));
    }
    Serial.print(F("Updated balance: "));
    Serial.println((char*)buffer);
    Tamount = 0;
    
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
}

// Function to dump UID in HEX format
void dump_byte_array(byte *buffer, byte bufferSize) {
    for (byte i = 0; i < bufferSize; i++) {
        Serial.print(buffer[i] < 0x10 ? " 0" : " ");
        Serial.print(buffer[i], HEX);
    }
}
