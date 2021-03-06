open Cil
module H = Hashtbl
module P = Printf	     
module L = List
module CM = Common	     


let stderrVi = CM.mkVi ~ftype:(TPtr(TVoid [], [])) "_coverage_fout"
(*
  walks over AST and preceeds each stmt with a printf that writes out its sid
  create a stmt consisting of 2 Call instructions
  fprintf "_coverage_fout, sid"; 
  fflush();
 *)
      
class coverageVisitor = object(self)
  inherit nopCilVisitor

  method private create_fprintf_stmt (sid : CM.sid_t) :stmt = 
  let str = P.sprintf "%d\n" sid in
  let stderr = CM.expOfVi stderrVi in
  let instr1 = CM.mkCall "fprintf" [stderr; Const (CStr(str))] in 
  let instr2 = CM.mkCall "fflush" [stderr] in
  mkStmt (Instr([instr1; instr2]))
    
  method vblock b = 
    let action (b: block) :block= 
      let insert_printf (s: stmt): stmt list = 
	if s.sid > 0 then [self#create_fprintf_stmt s.sid; s]
	else [s]
      in
      let stmts = L.map insert_printf b.bstmts in 
      {b with bstmts = L.flatten stmts}
    in
    ChangeDoChildrenPost(b, action)
      
  method vfunc f = 
    let action (f: fundec) :fundec = 
      (*print 0 when entering main so we know it's a new run*)
      if f.svar.vname = "main" then (
	f.sbody.bstmts <- [self#create_fprintf_stmt 0] @ f.sbody.bstmts
      );
      f
    in
    ChangeDoChildrenPost(f, action)
end
			  
(* main *)
(*Example:
/preproc.exe /var/tmp/CETI2_XhtAbh/MedianBad1.c mainQ correctQ /var/tmp/CETI2_XhtAbh/MedianBad1.c.preproc.c /var/tmp/CETI2_XhtAbh/MedianBad1.c.ast

*)
let () = begin
    initCIL();
    Cil.lineDirectiveStyle:= None; (*reduce code, remove all junk stuff*)

    let src = Sys.argv.(1) in
    let mainQName = Sys.argv.(2) in
    let correctQName = Sys.argv.(3) in    
    let preprocSrc = Sys.argv.(4) in     
    let astFile = Sys.argv.(5) in     

    let ast = Frontc.parse src () in

    visitCilFileSameGlobals (new CM.everyVisitor) ast;
    visitCilFileSameGlobals (new CM.breakCondVisitor :> cilVisitor) ast;
    
    let mainFd:fundec = CM.findFun ast "main" in
    let mainQFd:fundec = CM.findFun ast mainQName in
    let correctQFd:fundec = CM.findFun ast correctQName in    

    let ignoreFuns:CM.SS.t =
      L.fold_right CM.SS.add ["main" ; mainQName; correctQName] CM.SS.empty in

    (*add stmt id*)
    let stmtHt = H.create 1024 in
    visitCilFileSameGlobals (new CM.numVisitor stmtHt ignoreFuns :> cilVisitor) ast;

    CM.writeSrc preprocSrc ast;
    CM.write_file_bin astFile (ast, mainFd, mainQFd, correctQFd, stmtHt)
end
