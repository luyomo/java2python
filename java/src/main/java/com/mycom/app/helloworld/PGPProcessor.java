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

	    FileInputStream keyIn = new FileInputStream("/home/pi/workspace/hello-world/java/public-key.gpg");
	    File outfile = new File("/tmp/encryption.txt");

	    fo = new FileOutputStream(outfile, false);   // What the false mean
	    peDG = new PGPEncryptedDataGenerator(PGPEncryptedData.AES_256, true, new SecureRandom(), "BC");

	    peDG.addMethod(readPublicKey(keyIn));
	    System.out.println("Read key is done");

	    peOS = peDG.open(fo, new byte[buf_sz]);

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
