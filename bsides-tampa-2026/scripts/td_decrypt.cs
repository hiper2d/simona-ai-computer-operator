using System;
using System.IO;
using System.Reflection;

class Decryptor {
    static void Main() {
        // Load the malicious .NET assembly without running any of its code
        byte[] asmBytes = File.ReadAllBytes("/tmp/td_embedded_pe_1223.bin");
        Assembly asm = Assembly.Load(asmBytes);
        Type cipher = asm.GetType("SpaceTravel.Cipher");
        MethodInfo decrypt = cipher.GetMethod("Decrypt", BindingFlags.Public | BindingFlags.Static);

        // Reproduce the password: new Random(0x5A4D).NextBytes(byte[32]) -> base64
        // (0x5A4D = the "MZ" DOS magic of vbc.exe interpreted as a little-endian uint16)
        byte[] pw = new byte[32];
        new Random(0x5A4D).NextBytes(pw);
        string passphrase = Convert.ToBase64String(pw);
        Console.WriteLine("passphrase: " + passphrase);

        // Read the giant ciphertext base64 string from the assembly's #US heap.
        // We pulled it earlier; keep it in a separate file to dodge command-line length issues.
        string ct = File.ReadAllText("/tmp/td_ciphertext.b64").Trim();
        Console.WriteLine("ct length: " + ct.Length);

        // Call Cipher.Decrypt(ct, passphrase) -> returns base64(plaintext PE)
        string decryptedB64 = (string)decrypt.Invoke(null, new object[]{ct, passphrase});
        Console.WriteLine("decrypted (b64) length: " + decryptedB64.Length);

        // Base64 -> actual PE bytes
        byte[] pe = Convert.FromBase64String(decryptedB64);
        File.WriteAllBytes("/tmp/td_finalstage.bin", pe);
        Console.WriteLine("wrote " + pe.Length + " bytes -> /tmp/td_finalstage.bin");
        Console.WriteLine("first 8 bytes: " + BitConverter.ToString(pe, 0, Math.Min(8, pe.Length)));
    }
}
