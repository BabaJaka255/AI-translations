// Headless (-process -noanalysis): clear "noreturn" on the given memset-like functions, re-disassemble,
// then decompile the listed functions.  args: outdir noreturn_addr[,..] func_addr[,..]
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*;
public class DecompSome extends GhidraScript {
  public void run() throws Exception {
    String[] a=getScriptArgs(); String out=a[0]; new File(out).mkdirs();
    for (String s: a[1].split(",")) { Function f=getFunctionAt(toAddr(Long.decode(s))); if (f!=null) f.setNoReturn(false); }
    for (String s: a[2].split(",")) {
      Address ad=toAddr(Long.decode(s));
      clearListing(ad, ad.add(0x1400));
      new DisassembleCommand(ad,null,true).applyTo(currentProgram,monitor);
      Function f=getFunctionAt(ad); if (f==null) f=createFunction(ad,null);
      ghidra.app.cmd.function.CreateFunctionCmd c=null;
      f=getFunctionAt(ad);
      ghidra.program.model.address.AddressSet body=new ghidra.program.model.address.AddressSet();
      DecompInterface di=new DecompInterface(); di.openProgram(currentProgram);
      DecompileResults r=di.decompileFunction(f,60,monitor);
      String txt=(r!=null&&r.decompileCompleted())?r.getDecompiledFunction().getC():"// failed\n";
      try (PrintWriter w=new PrintWriter(new File(out,s+".c"))) { w.print(txt); }
    }
  }
}
