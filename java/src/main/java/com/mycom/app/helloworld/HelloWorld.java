package com.mycom.app.helloworld;

import java.security.NoSuchAlgorithmException;
import java.security.InvalidKeyException;
import javax.crypto.NoSuchPaddingException;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.BadPaddingException;
import javax.crypto.SecretKey;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;

public class HelloWorld{
    public String sayHello(){
        return "Hello World";
    }

    private static final String secretKeyString = "16df7fa2641fa89d";

    public static String encryptDes(String clearText){
	    String encryptedHexString = "";

	    SecretKey secretKey = new SecretKeySpec(HexStringToBytes(secretKeyString), "DES");

            byte[] clearTextByte = clearText.getBytes();

	    Cipher cipher;
	    try {
		    cipher = Cipher.getInstance("DES");
		    cipher.init(Cipher.ENCRYPT_MODE, secretKey);
		    encryptedHexString = bytesToHexString(cipher.doFinal(clearTextByte));
		    return encryptedHexString;
	    } catch(NoSuchAlgorithmException e) {
		    e.printStackTrace();
	    } catch(NoSuchPaddingException e) {
		    e.printStackTrace();
	    } catch(InvalidKeyException e) {
		    e.printStackTrace();
	    } catch(IllegalBlockSizeException e) {
		    e.printStackTrace();
	    } catch(BadPaddingException e) {
		    e.printStackTrace();
	    }

	    return null;
    }  

    public static String decryptDes(String encryptedHexText) {
            Cipher cipher; 
	    try {
		    cipher = Cipher.getInstance("DES");
		    cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(HexStringToBytes(secretKeyString), "DES") );
		    byte[] decryptedByte = cipher.doFinal(HexStringToBytes(encryptedHexText));
		    String decryptedText = new String(decryptedByte);
		    return decryptedText;
	    } catch(NoSuchAlgorithmException e) {
		    e.printStackTrace();
	    } catch(NoSuchPaddingException e) {
		    e.printStackTrace();
	    } catch(InvalidKeyException e) {
		    e.printStackTrace();
	    } catch(IllegalBlockSizeException e) {
		    e.printStackTrace();
	    } catch(BadPaddingException e) {
		    e.printStackTrace();
	    }
	    return null;
    }

    public static void main(String[] args){
	System.out.println(args[0]);
	System.out.println("*******************************");
        System.out.println(new HelloWorld().sayHello());
	String testInput = args[0];
	String encryptedText = encryptDes(testInput);
	System.out.println("\n********** The original data :");
	System.out.println(testInput);
	System.out.println("\n********** The encrypted text here is :");
	System.out.println(encryptedText);
	System.out.println("\n********** The decrypted text here is :");
	String decryptedText = decryptDes(encryptedText);
	System.out.println(decryptedText);
    }

    public static String bytesToHexString(byte[] fromByte) {
        StringBuilder hexStrBuilder = new StringBuilder();

	for (int i = 0; i < fromByte.length; i++) {
		if((fromByte[i] & 0xff) < 0x10){
		    hexStrBuilder.append("0");
		}
		hexStrBuilder.append(Integer.toHexString(0xff & fromByte[i]));
	}
	return hexStrBuilder.toString();
    }

    public static byte[] HexStringToBytes(String fromHexStr){
	    byte[] toByte = new byte[fromHexStr.length() / 2];
	    for (int i = 0; i < toByte.length; i++) {
		    toByte[i] = (byte) Integer.parseInt(fromHexStr.substring( i * 2, ( i + 1 ) * 2), 16);
	    }
	    return toByte;
    }
}
