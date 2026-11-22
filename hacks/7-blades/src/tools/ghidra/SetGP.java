// Pre-script: set $gp to a constant over the whole program (arg: hex value).
import ghidra.app.script.GhidraScript;
import ghidra.program.model.lang.Register;
import java.math.BigInteger;
public class SetGP extends GhidraScript {
  public void run() throws Exception {
    BigInteger v=new BigInteger(getScriptArgs()[0].replace("0x",""),16);
    Register gp=currentProgram.getRegister("gp");
    var mem=currentProgram.getMemory();
    for (var b: mem.getBlocks()) if (b.isExecute()||b.isInitialized())
      currentProgram.getProgramContext().setValue(gp,b.getStart(),b.getEnd(),v);
  }
}
