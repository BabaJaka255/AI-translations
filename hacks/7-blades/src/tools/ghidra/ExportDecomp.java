// Headless: export every function's decompiled C to <outdir>/<entry>.c plus an index.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import java.io.*;
public class ExportDecomp extends GhidraScript {
  public void run() throws Exception {
    String out=getScriptArgs()[0]; new File(out).mkdirs();
    DecompInterface di=new DecompInterface(); di.openProgram(currentProgram);
    PrintWriter idx=new PrintWriter(new File(out,"index.tsv"));
    for (Function f: currentProgram.getFunctionManager().getFunctions(true)) {
      if (monitor.isCancelled()) break;
      DecompileResults r=di.decompileFunction(f,30,monitor);
      String c=(r!=null&&r.decompileCompleted())?r.getDecompiledFunction().getC():"// failed\n";
      String n=f.getEntryPoint().toString();
      try (PrintWriter w=new PrintWriter(new File(out,n+".c"))) { w.print(c); }
      idx.println(n+"\t"+f.getName()+"\t"+f.getBody().getNumAddresses());
    }
    idx.close();
  }
}
