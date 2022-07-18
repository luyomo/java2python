package com.mycom.app.helloworld;

//import java.security.NoSuchAlgorithmException;
//import java.security.InvalidKeyException;
//import javax.crypto.NoSuchPaddingException;
//import javax.crypto.IllegalBlockSizeException;
//import javax.crypto.BadPaddingException;
//import javax.crypto.SecretKey;
//import javax.crypto.Cipher;
//import javax.crypto.spec.SecretKeySpec;
//import java.util.Base64;


import org.bouncycastle.jce.provider.BouncyCastleProvider;
import java.security.Security;
import org.bouncycastle.openpgp.*;
import java.io.*;
import java.util.Arrays;
import java.util.Date;
import java.util.Iterator;
import java.security.Security;
import java.security.SecureRandom;

public class PGPProcessor{
    public String sayHello(){
        return "Hello World";
    }

    public static void main(String[] args){
        System.out.println(new HelloWorld().sayHello());
	try {
	    encryptFile();
	} catch(Exception e){
	    e.printStackTrace();
//	    throw e;
	}
    }

    public static void decryptFile() throws Exception{
        PGPPrivateKey sKey              = null;
        PGPPublicKeyEncryptedData pbe   = null;
        PGPEncryptedDataList enc        = null;
        FileInputStream inPrivKey       = null;
        InputStream clear               = null;
        PGPObjectFactory plainFact      = null;
        ByteArrayOutputStream baos      = null;

        try {
            Security.addProvider(new BouncyCastleProvider());
            
	    String strSecuretKeyFile = "/home/pi/.ssh/gpg_test.pub";
	    String strPGPFile = "/tmp/encryption.txt";
            String strSecuretKeyPhrase = "1234Abcd";

	    inPrivKey = new FileInputStream(strSecuretKeyFile);
	    InputStream insPGPFile = new BufferedInputStream(new FileInputStream(strPGPFile));
	    PGPObjectFactory pgpF = new PGPObjectFactory(PGPUtil.getDecoderStream(insPGPFile));
	    Object o = pgpF.nextObject();
	    enc = o instanceof PGPEncryptedDataList ? (PGPEncryptedDataList) o :(PGPEncryptedDataList) pgpF.nextObject();
	    Iterator it = enc.getEncryptedDataObjects();

	    while (sKey == null && it.hasNext()){
                pbe = (PGPPublicKeyEncryptedData) it.next();
		sKey = findSecretKey(inPrivKey, pbe.getKeyID(), strSecuretKeyPhrase.toCharArray());
	    }

	    if (sKey == null) {
                throw new IllegalArgumentException("Secret key for message not found.");
	    }
	    System.out.println("Read Secret Key is done");

	    clear = pbe.getDataStream(sKey, "BC");
	    plainFact = new PGPObjectFactory(clear);
	    Object message = plainFact.nextObject();

	    if (message instanceof PGPCompressedData) {
                PGPLiteralData ld = (PGPLiteralData) message;
		InputStream unc = ld.getInputStream();
		int ch;
		while ( (ch = unc.read()) >= 0) {
		    baos.write(ch);
		}
	    } else if (message instanceof PGPOnePassSignatureList){
	        throw new PGPException("encrypted message contains a signed message - not literal data.");
	    } else {
                throw new PGPException("message is not a simple encrypted file - type unknown");
	    }

	    if (pbe.isIntegrityProtected()) {
	        if (!pbe.verify()) {
		    System.out.println("message failed integrity check");
		}
	    }else{
                System.out.println("no message integrity check");
	    }

	    // Clear tet File Creation
	    String strTxtFile = "/tmp/test.txt";
	    baos.writeTo(new FileOutputStream(new File(strTxtFile)));
	    System.out.println("Decryption is done");
        } catch (PGPException e){
            e.printStackTrace();
            throw e;
        } catch (IOException e) {
            e.printStackTrace();
            throw e;
        }
    }

    public static void encryptFile() throws Exception{
        int buf_sz = 1<<14;

	PGPEncryptedDataGenerator peDG = null;
	PGPCompressedDataGenerator pcDG = null;
	PGPLiteralDataGenerator plDG = null;
	FileOutputStream fo = null;
	OutputStream peOS = null;
	OutputStream pcOS = null;
	OutputStream plOS = null;

	OutputStreamWriter ow = null;
	BufferedWriter bw = null;
	BufferedReader br = null;

	FileInputStream in = null;
	InputStreamReader inSrd = null;

	try {
	    Security.addProvider(new BouncyCastleProvider());

            // Generate the random seeds
	    SecureRandom randomKey = new SecureRandom();
            byte[] bytes = randomKey.generateSeed(16);;
	    System.out.println(randomKey.toString());
            randomKey.nextBytes(bytes);
            System.out.println(Arrays.toString(bytes));
            randomKey.nextBytes(bytes);
            System.out.println(Arrays.toString(bytes));

            // Read public key
	    FileInputStream keyIn = new FileInputStream("/home/pi/workspace/hello-world/java/public-key.gpg");

            // Open the output file stream
	    File outfile = new File("/tmp/encryption.txt");
	    fo = new FileOutputStream(outfile, false);   // What the false mean

            // Generate the random key
	    peDG = new PGPEncryptedDataGenerator(PGPEncryptedData.AES_256, true, new SecureRandom(), "BC");

	    peDG.addMethod(readPublicKey(keyIn));
	    System.out.println("Read key is done");

            // Open the input text
	    peOS = peDG.open(fo, new byte[buf_sz]);

            // Generate the instance of hte compressed data
	    pcDG = new PGPCompressedDataGenerator(PGPCompressedData.ZIP);
            pcOS = pcDG.open(peOS);

	    plDG = new PGPLiteralDataGenerator();
	    plOS = plDG.open(pcOS, PGPLiteralData.BINARY, outfile.getName(), new Date(), new byte[buf_sz]);

	    System.out.println("write data start");

	    // Build a writer ontop
	    //ow = new OutputStreamWriter(plOS, strOutEncoding);
	    ow = new OutputStreamWriter(plOS, "UTF-8");
	    bw = new BufferedWriter(ow);

	    // Read vlear text file
	    in = new FileInputStream("/tmp/rawdata.txt");
	    inSrd = new InputStreamReader(in, "UTF-8");
	    br = new BufferedReader(inSrd);

	    // Read first row
	    String strLine = br.readLine();

	    // Loop to write PGP file
	    while(strLine != null) {
	        bw.write(strLine + "\r\n");
		strLine = br.readLine();
	    }

	    System.out.println("Encryption is done");



	} catch (PGPException e){
	    e.printStackTrace();
	    throw e;
	} catch (IOException e) {
	    e.printStackTrace();
	    throw e;
	}
//       	catch (Exception e) {
//	    e.printStackTrace();
//	    throw e;
//	}
    }

    private static PGPPrivateKey findSecretKey(InputStream keyIn, long keyID, char[] pass){
	    try {
		PGPSecretKeyRingCollection pgpSec = new PGPSecretKeyRingCollection(PGPUtil.getDecoderStream(keyIn));
		System.out.println("keyID: " + keyID);
		PGPSecretKey pgpSecKey = pgpSec.getSecretKey(keyID);
		return pgpSecKey != null?pgpSecKey.extractPrivateKey(pass, "BC"):null;
	    }catch (Exception e) {
		e.printStackTrace();
	    } 
	    return null;
    }

    private static PGPPublicKey readPublicKey(InputStream in) throws IOException, PGPException {
        try {
            System.out.println("++++++++++++++++++++++++++");
	    in = PGPUtil.getDecoderStream(in);
            System.out.println(";;;;;;;;;;;;;;;;;;;;;;;;;+");
	    PGPPublicKeyRingCollection pgpPub = new PGPPublicKeyRingCollection(in);

	    PGPPublicKey key = null;

	    Iterator rIt = pgpPub.getKeyRings();

	    while (key == null && rIt.hasNext()) {
                System.out.println("Got the key here ");
                PGPPublicKeyRing kRing = (PGPPublicKeyRing) rIt.next();
		Iterator kIt = kRing.getPublicKeys();

		while (key == null && kIt.hasNext()) {
		    PGPPublicKey k = (PGPPublicKey) kIt.next();

		    if (k.isEncryptionKey()) {
	                key = k;
		    }
		}
	    }
            System.out.println("---------------------------");

	    if (key == null) {
		throw new IllegalArgumentException("Can't find encryption key in key ring.");
	    }
	    return key;
        } catch (PGPException ex) {
	    ex.printStackTrace();
	} catch (Exception e) {
	    e.printStackTrace();
	}
	return null;
    }
}
