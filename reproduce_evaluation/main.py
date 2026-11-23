"""Explicit original-stage runner. Default prints commands; --execute opts into computation."""
from pathlib import Path
import argparse,subprocess,sys,json,ast
R=Path(__file__).resolve().parent
jobs={'train_B':('abcd_pilot_v1','train_abcd_pilot.py',['--stage','train','--methods','B','--device','cpu']), 'fit_CVAE_LOCAL':('baseline_pilot_v1','run_baseline_pilot.py',['--stage','fit','--device','cpu']), 'train_repeats':('bcvae_repeats_v1','run_bcvae_repeats.py',['--stage','train','--device','cpu']), 'neural_generate':('wing_requirement_extension_v1','run_requirement_extension.py',['--stage','generate','--device','cpu']), 'neural_evaluate':('wing_requirement_extension_v1','run_requirement_extension.py',['--stage','evaluate','--device','cpu']), 'neural_summarize':('wing_requirement_extension_v1','run_requirement_extension.py',['--stage','summarize','--device','cpu']), 'local_generate':('wing_local_comparison_v1','run_local_comparison.py',['--stage','generate']), 'local_evaluate':('wing_local_comparison_v1','run_local_comparison.py',['--stage','evaluate']), 'local_summarize':('wing_local_comparison_v1','run_local_comparison.py',['--stage','summarize'])}
p=argparse.ArgumentParser();p.add_argument('stage',choices=list(jobs)+['audit','postprocess']);p.add_argument('--execute',action='store_true');p.add_argument('--font-dir');a=p.parse_args()
if a.stage=='audit':
 files=list((R/'experiments').rglob('*.py'))
 for f in files:ast.parse(f.read_text(encoding='utf-8-sig'),filename=str(f))
 missing=[]
 for f in (R/'experiments').rglob('PACKAGE_SHA256.json'):
  import hashlib
  for name,h in json.loads(f.read_text()).items():
   q=f.parent/name
   if not q.is_file() or hashlib.sha256(q.read_bytes()).hexdigest()!=h:missing.append(str(q.relative_to(R)))
 report={'python_files_parsed':len(files),'hash_mismatches':missing,'training_executed':False,'generation_executed':False,'aerodynamics_executed':False}
 (R/'static_workflow_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(bool(missing))
if a.stage=='postprocess':
 commands=[[sys.executable,str(R/'figures_reproduction/scripts/plot_all.py')],[sys.executable,str(R/'rebuild_supplement_tables.py')]]
 if a.font_dir:
  for cmd in commands:cmd+=['--font-dir',str(Path(a.font_dir).resolve())]
 cwd=R
else:
 folder,script,args=jobs[a.stage];cwd=R/'experiments'/folder
 out=R/'rerun_outputs'/folder
 commands=[[sys.executable,str(cwd/script),*args,'--out',str(out)]]
for cmd in commands:
 print('cwd:',cwd);print(subprocess.list2cmdline(cmd))
 if a.execute:subprocess.run(cmd,cwd=cwd,check=True)
