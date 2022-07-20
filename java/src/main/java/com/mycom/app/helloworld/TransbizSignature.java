package com.mycom.app.helloworld;

import java.io.BufferedInputStream;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.security.Security;
import java.text.SimpleDateFormat;
import java.util.Iterator;
import java.util.Properties;

import org.bouncycastle.bcpg.ArmoredOutputStream;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.openpgp.PGPCompressedData;
import org.bouncycastle.openpgp.PGPException;
import org.bouncycastle.openpgp.PGPObjectFactory;
import org.bouncycastle.openpgp.PGPPrivateKey;
import org.bouncycastle.openpgp.PGPPublicKey;
import org.bouncycastle.openpgp.PGPPublicKeyRingCollection;
import org.bouncycastle.openpgp.PGPSecretKey;
import org.bouncycastle.openpgp.PGPSecretKeyRing;
import org.bouncycastle.openpgp.PGPSecretKeyRingCollection;
import org.bouncycastle.openpgp.PGPSignature;
import org.bouncycastle.openpgp.PGPSignatureGenerator;
import org.bouncycastle.openpgp.PGPSignatureList;
import org.bouncycastle.openpgp.PGPUtil;
import org.bouncycastle.openpgp.operator.jcajce.JcaPGPContentSignerBuilder;
import org.bouncycastle.openpgp.operator.jcajce.JcaPGPContentVerifierBuilderProvider;
import org.bouncycastle.openpgp.operator.jcajce.JcePBESecretKeyDecryptorBuilder;

public class TransbizSignature {
    public static void main(String[] args){
        try {
            System.out.println("Hello world ");

            // -- checkFileExiting
            // String res = checkFileExiting("/tmp/encryption.txt");

            // -- getConfigSettings
            // Properties prop = getConfigSettings("/home/pi/workspace/hello-world/java/test.SFTP.properties");
            // System.out.println("The config value is " + prop.getProperty("Key"));

            // -- SignatureGeneration
            String sig = SignatureGeneration("/tmp/rawdata.txt", "/home/pi/workspace/hello-world/java/private-key.pgp", "1234Abcd");
            System.out.println("The siganature is " + sig);

            String veri = SignatureVerification("/tmp/rawdata.txt", "/home/pi/workspace/hello-world/java/public-key.gpg", sig);
            System.out.println("The verification here is " + veri);

            veri = SignatureVerification("/tmp/encryption.txt", "/home/pi/workspace/hello-world/java/public-key.gpg", sig);
            System.out.println("The verification here is " + veri);
        } catch(Exception e){
            e.printStackTrace();
        }
    }

    public static String checkFileExiting(String strfilename) throws Exception{
        File f = null;
        try {
            f = new File(strfilename);
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
            String StrReturn = sdf.format(f.lastModified());
            System.out.println("LasModified : " + StrReturn);
            return StrReturn;
        }catch(Exception ex){
            ex.printStackTrace();
        }finally{
            f=null;
        };
        return null;
    }

    public static Properties getConfigSettings(String PropertiesURL) throws Exception {
        try {
            Properties conf = new Properties();
	    if(PropertiesURL == null){
                PropertiesURL = new File("").getAbsolutePath() + File.separator + "SFTP.properties";
	    }
            System.out.println("The file name is " + PropertiesURL);

	    try {
                conf.load(new FileInputStream(PropertiesURL));
	    } catch(IOException e) {
                System.err.println("Cannot open " + new File("").getAbsolutePath()+File.separator+"SFTP.properties");
		e.printStackTrace();
		throw e;
	    }
	    return conf;
	}catch(Exception ex) {
            ex.printStackTrace();
	    throw ex;
	}
    }

    public static String SignatureVerification(String strFilename, String strPublicKey, String strSignature) throws Exception{
        InputStream vkeyIn    = null;
        InputStream vfileIn   = null;
        InputStream sigfileIn = null;
        PGPSignatureList   p3 = null;

	try {
            sigfileIn = new ByteArrayInputStream((strSignature).getBytes("UTF8"));
	    InputStream in = PGPUtil.getDecoderStream(sigfileIn);

	    PGPObjectFactory pgpFact = new PGPObjectFactory(in);
	    Object o = pgpFact.nextObject();
	    if(o instanceof PGPCompressedData) {
                PGPCompressedData c1 = (PGPCompressedData)o;
		pgpFact = new PGPObjectFactory(c1.getDataStream());
                p3 = (PGPSignatureList)pgpFact.nextObject();
	    } else {
                p3 = (PGPSignatureList)o;
	    }
	    PGPSignature sig = p3.get(0);

	    vkeyIn = new BufferedInputStream(new FileInputStream(strPublicKey));
	    PGPPublicKeyRingCollection pgpPubRingCollection = new PGPPublicKeyRingCollection(PGPUtil.getDecoderStream(vkeyIn));
	    vfileIn = new BufferedInputStream(new FileInputStream(strFilename));
	    PGPPublicKey key = pgpPubRingCollection.getPublicKey(sig.getKeyID());

	    sig.init(new JcaPGPContentVerifierBuilderProvider().setProvider("BC"), key);
	    int ch;
	    while ((ch = vfileIn.read()) >= 0){
                sig.update((byte)ch);
	    }

	    if (sig.verify()) {
                System.out.println("signature verified.");
		return "Y";
	    }else{
                System.out.println("signature verification failed.");
		return "N";
	    }
	} catch (Exception e) {
            e.printStackTrace();
	} finally {
            try {
                if(vkeyIn!=null) vkeyIn.close();
	    } catch(IOException e) {
		e.printStackTrace();
	    }

	    try {
                vfileIn.close();
	    } catch(IOException e) {
                e.printStackTrace();
	    }

	    try {
                sigfileIn.close();
	    } catch(IOException e) {
                e.printStackTrace();
	    }
	}
	return "N";
    }

    static PGPSecretKey readSecretKey(String fileName) throws IOException, PGPException{
        InputStream keyIn = new BufferedInputStream(new FileInputStream(fileName));
	PGPSecretKey secKey = readSecretKey(keyIn);
	keyIn.close();
	return secKey;
    }

    public static PGPSecretKey readSecretKey(InputStream input) throws IOException, PGPException {
        PGPSecretKeyRingCollection pgpSec = new PGPSecretKeyRingCollection(PGPUtil.getDecoderStream(input));

	Iterator keyRingIter = pgpSec.getKeyRings();
	while(keyRingIter.hasNext()) {
            PGPSecretKeyRing keyRing = (PGPSecretKeyRing)keyRingIter.next();

	    Iterator keyIter = keyRing.getSecretKeys();
	    while (keyIter.hasNext()){
                PGPSecretKey key = (PGPSecretKey)keyIter.next();

		if (key.isSigningKey()){
		    return key;
		}
	    }
	}

	throw new IllegalArgumentException("Can't find signing key in key ring");
    }

    public static String SignatureGeneration(String strFilename, String strSecretKey, String strPhrase) throws Exception {
        InputStream keyIn = null;
	InputStream fileIn = null;
	String strSignature = null;

	try {
            System.out.println(strFilename);
	    keyIn = new BufferedInputStream(new FileInputStream(strSecretKey));
	    Security.addProvider(new BouncyCastleProvider());
	    PGPSecretKey pgpSec = readSecretKey(keyIn);
	    PGPPrivateKey pgpPrivKey = pgpSec.extractPrivateKey(new JcePBESecretKeyDecryptorBuilder().setProvider("BC").build(strPhrase.toCharArray()));

	    PGPSignatureGenerator sGen = new PGPSignatureGenerator(new JcaPGPContentSignerBuilder(pgpSec.getPublicKey().getAlgorithm(), PGPUtil.SHA512).setProvider("BC"));
	    sGen.init(PGPSignature.BINARY_DOCUMENT, pgpPrivKey);
	    fileIn = new BufferedInputStream(new FileInputStream(strFilename));

	    int ch;
	    while((ch = fileIn.read()) >= 0){
	        sGen.update((byte)ch);
	    }

	    PGPSignature Signature = sGen.generate();
	    ByteArrayOutputStream byteOut = new ByteArrayOutputStream();
	    ArmoredOutputStream Armout = new ArmoredOutputStream(byteOut);
	    Signature.encode(Armout);

	    Armout.close();
	    strSignature = byteOut.toString("UTF8");
	    System.out.println(strSignature);
	} catch(Exception e) {
	    e.printStackTrace();
	} finally {
	    try {
	        fileIn.close();
	    } catch (IOException e) {
	        e.printStackTrace();
	    }

	    try {
	        keyIn.close();
	    } catch(IOException e) {
	        e.printStackTrace();
	    }
	}

	return strSignature;
    }
}
