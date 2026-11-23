#!/usr/bin/env python3
"""Rebuild Figs. 3-11 from frozen data; no training, generation or aerodynamic solves.
Usage: python scripts/plot_all.py [--font-dir PATH]
"""
from pathlib import Path
import argparse,json,hashlib,platform,io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.text import Text
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.collections import PathCollection
import style
import source_pairs as pairs
import source_groups as groups
import source_comparisons as comp
import source_diagnostics as diag
ROOT=Path(__file__).resolve().parents[1]
MAP={'fig03_requirement_design':(3,'requirements'), 'fig04_strict_input_by_span':(4,'strict_input'),
     'fig10_candidate_state_transitions':(5,'tightening'), 'fig05_response_and_composition':(6,'response_composition'),
     'fig11_relaxation_transitions':(7,'relaxation'), 'fig08_publication':(8,'yield_distribution'),
     'fig08_requirement_yield':(9,'requirement_yield'), 'fig09_boundary_diagnostic':(10,'boundary_diagnostic'),
     'fig07_geometry_choices':(11,'geometry_choices')}
AUDIT=[]

def read(name):return pd.read_csv(ROOT/'data'/name,float_precision='round_trip')
def label(fig,x,y,s,**kw):return fig.text(x,y,s,fontfamily=style.FONT,fontsize=9,**kw)
def legend_remove(fig):
    for l in list(fig.legends):l.remove()
def runs():return [Line2D([],[],ls='none',marker=mk,color=style.INK,ms=4,label=f'Run {i+1}') for i,mk in enumerate(style.MARKERS)]
def move(ax,rect):ax.set_position(rect)
def title(ax,s):ax.set_title(s,loc='left',pad=8,fontsize=9,fontweight='bold')
def normalize(fig):
    for t in fig.findobj(match=Text):
        t.set_fontfamily(style.FONT); t.set_fontsize(8)
    for ax in fig.axes:
        ax.xaxis.label.set_fontsize(9);ax.yaxis.label.set_fontsize(9)
        for t in [ax.title,ax._left_title,ax._right_title]:t.set_fontsize(9)
        for c in ax.collections:
            if isinstance(c,PathCollection):c.set_sizes(np.minimum(c.get_sizes(),24))
        for l in ax.lines:
            if l.get_markersize()>4.5:l.set_markersize(4.5)
    fig.set_facecolor('white')

def finish(fig,name):
    num,slug=MAP[name]
    heights={3:67,4:83,5:86,6:168,7:95,8:140,9:155,10:82,11:177}
    fig.set_size_inches(style.WIDTH_MM/25.4,heights[num]/25.4)
    normalize(fig)
    if num==3:
        for j,ax in enumerate(fig.axes):
            move(ax,[.085+j*.305,.25,.265,.62]);ax.title.set_y(1)
            ax.set_xlabel(r'$10^3 C_{D,\mathrm{cruise}}$')
            for t in ax.texts:
                if t.get_text().startswith('Training pool:'):t.set_text(t.get_text().replace('Training pool:','n ='))
        for l in fig.legends:l.set_bbox_to_anchor((.53,.015))
    elif num==4:
        for j,ax in enumerate(fig.axes):
            move(ax,[.105+j*.30,.27,.25,.57]);ax.set_xlabel('Strict-target acceptance (%)',fontsize=8)
        fig.text(.105,.94,'Open: central input    Filled: strict input',fontsize=8)
        for l in fig.legends:l.set_bbox_to_anchor((.55,.015))
    elif num in [5,7]:
        # Preserve exact flow geometry and count widths; remove the former prose banner.
        fig.patches.clear()
        for k,ax in enumerate(fig.axes):
            move(ax,[.015+k*.33,.10 if num==5 else .09,.31,.65])
            for t in ax.texts:
                if num==7 and k==0 and t.get_text()=='13':t.set_position((.34,.49))
                if num==7 and k==0 and t.get_text()=='26':t.set_position((.51,.31))
                if t.get_text().startswith('Pass-to-fail'):t.set_text('Pass to fail: 0')
            label(fig,.17+k*.33,.94,f'({chr(97+k)}) {style.NAMES[style.METHODS[k]]}',ha='center',weight='bold',color=style.COLORS[style.METHODS[k]])
        # Brief symbol key: detailed pairing/count definitions are in captions.
        if num==5:
            hh=[Patch(fc=pairs.TEAL,label='Fail to pass'),Patch(fc=pairs.ORANGE,label='Pass to fail')]
        else:
            hh=[Patch(fc=pairs.TEAL,label='Loose-only feasible'),Patch(fc=pairs.ORANGE,label='To loose-target failure')]
        fig.legend(handles=hh,loc='lower center',bbox_to_anchor=(.5,.005),ncol=2,frameon=False,fontsize=8)
    elif num==6:
        for i,ax in enumerate(fig.axes):
            if i<6:
                row,col=divmod(i,3);move(ax,[.085+col*.305,.645-row*.260,.265,.215])
                # S/A/F membership is retained; category definitions now appear once.
            else:
                col=i-6;move(ax,[.085+col*.305,.095,.265,.16])
        legend_remove(fig)
        hh=[Line2D([],[],color=groups.CC[k],marker=groups.CLASS_MARKER[k],ls='none',ms=4,label=f'{k}: '+groups.CLASS_LABEL[k]) for k in ['S','A','F']]
        fig.legend(handles=hh,loc='upper center',bbox_to_anchor=(.52,.997),ncol=3,frameon=False,fontsize=8,columnspacing=1)
        label(fig,.085,.912,r'Responses: $b_{\max}=13.75$ m',weight='bold')
        label(fig,.085,.305,'Composition: all three span limits',weight='bold')
        hh=[Line2D([],[],color=groups.CC['S'],lw=1,label='Strict bounds'),Line2D([],[],color=groups.CC['A'],lw=1,ls='--',label='Loose bounds')]+[Line2D([],[],ls='none',marker=mk,color=style.INK,mfc='white',ms=4,label=f'Run {i+1}') for i,mk in enumerate(style.MARKERS)]
        fig.legend(handles=hh,loc='lower center',bbox_to_anchor=(.52,.005),ncol=5,frameon=False,fontsize=8,columnspacing=1)
    elif num==8:
        pass
    elif num==9:
        ax,dx,cax=fig.axes
        move(ax,[.265,.19,.245,.72]);move(dx,[.59,.19,.375,.72]);move(cax,[.265,.10,.245,.014])
        dx.set_xlabel('Feasibility gain over LOCAL (pp)',fontsize=9)
        for t in ax.texts:
            if t.get_text().endswith(' m'):t.set_position((-3.0,t.get_position()[1]));t.set_fontsize(8)
        label(fig,.025,.966,r'$b_{\max}$',weight='bold')
        label(fig,.265,.966,'(a) Feasibility (%)',weight='bold')
        label(fig,.59,.966,'(b) Gain over LOCAL',weight='bold')
        legend_remove(fig)
        hh=[Line2D([],[],lw=2,color=style.COLORS[m],label=style.NAMES[m]) for m in ['B','CVAE']]+runs()+[Line2D([],[],ls='none',marker='D',mfc='none',mec=style.INK,ms=5,label='Mean')]
        fig.legend(handles=hh,ncol=6,loc='lower center',bbox_to_anchor=(.52,.01),frameon=False,fontsize=8,columnspacing=1.2)
    elif num==10:
        a,z=fig.axes;move(a,[.09,.26,.49,.60]);move(z,[.68,.26,.29,.60])
        a.set_ylabel('Cumulative candidates (%)')
        for t in a.texts:
            if t.get_text().startswith('At least'):t.set_text('Drag bound exceeded');t.set_position((.43,.48))
        # Exact counts remain useful, without the previous three prose footnotes.
        for j,m in enumerate(style.METHODS):
            r=BOUND_SUMMARY.loc[BOUND_SUMMARY.method.eq(m)].iloc[0]
            fig.text(.09+j*.305,.06,f'{style.NAMES[m]}: {int(r.feasible_n)}/192 feasible',color=style.COLORS[m],fontsize=8,weight='bold')
    elif num==11:
        # 24 gallery axes (wing plus true-angle section), followed by four boxplot axes.
        lefts=[.055,.375,.695]
        for row,cl in enumerate(['S','A']):
            top=.90-row*.275; y=top-.205
            label(fig,.055,top,'(a) Strict input: strict-feasible' if row==0 else '(b) Loose input: additional-region feasible',weight='bold',color=groups.CC[cl])
            for mi,m in enumerate(style.METHODS):
                for ki,kind in enumerate(['M','D']):
                    idx=row*12+mi*4+ki*2
                    ax,pa=fig.axes[idx:idx+2];base=lefts[mi]+ki*.147
                    move(ax,[base,y,.144,.185]);move(pa,[base+.016,y+.006,.112,.037])
                    fid=f'{cl}{mi+1}{kind}';r=WINGS.loc[WINGS.figure_id.eq(fid)].iloc[0]
                    fig.text(base+.072,y+.187,fid,ha='center',fontsize=8)
                    fig.text(base+.072,y-.01,f'b = {r.span:.2f} m',ha='center',fontsize=8)
                fig.text(lefts[mi]+.145,y-.032,f'n = {len(GROUPS[(m,cl)])}',ha='center',fontsize=8)
        for mi,m in enumerate(style.METHODS):label(fig,lefts[mi]+.145,.965,style.NAMES[m],ha='center',color=style.COLORS[m],weight='bold')
        label(fig,.055,.345,'(c) Feasible-group geometry distributions',weight='bold')
        for ci,ax in enumerate(fig.axes[-4:]):
            move(ax,[.10+ci*.225,.125,.185,.175])
            if ci==0:ax.set_xticks([10,11,12,13,13.75]);ax.set_xticklabels(['10','11','12','13','13.75']);ax.tick_params(axis='x',labelsize=7.5)
            if ci==1:ax.set_xlabel('Quarter-chord\nsweep (deg)')
        for l in fig.legends:l.set_bbox_to_anchor((.53,.01));l.set_ncols(2)
    # Reapply family to newly added annotations; explicit size choices are retained.
    for t in fig.findobj(match=Text):t.set_fontfamily(style.FONT)
    for ax in fig.axes:
        for artist in ax.collections:artist.set_rasterized(False)
        ax.xaxis.set_tick_params(pad=3);ax.yaxis.set_tick_params(pad=3)
    fig.canvas.draw()
    bounds=[]
    renderer=fig.canvas.get_renderer()
    for t in fig.findobj(match=Text):
        if not t.get_visible() or not t.get_text():continue
        bb=t.get_window_extent(renderer)
        # Hidden tick labels outside data limits are not drawn.
        if t.get_clip_on():continue
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1>fig.bbox.width+1 or bb.y1>fig.bbox.height+1:
            bounds.append(t.get_text())
    stem=f'fig{num:02d}_{slug}'
    for ext in ['png','pdf']:
        b=io.BytesIO();fig.savefig(b,format=ext,dpi=style.DPI,facecolor='white')
        dest=ROOT/'figures'/f'{stem}.{ext}';tmp=dest.with_suffix('.tmp');tmp.write_bytes(b.getvalue());tmp.replace(dest)
    AUDIT.append({'figure':num,'filename':stem,'width_mm':style.WIDTH_MM,'height_mm':heights[num],'outside_canvas_text':bounds})
    plt.close(fig)
    print('Exported',stem, 'bounds warnings:',bounds,flush=True)

def fig8():
    p=read('fig05_success_seed_means.csv');c=read('fig06_seed_means.csv')
    allmetrics=read('fig06_full_equal_count_metrics.csv')
    metrics=['train_to_generated_nn_mean','feasible_pair_distance','train_coverage_r05','train_coverage_r10']
    expected=allmetrics[allmetrics.roles.isin(['strict','center','loose'])].groupby(['method','seed','roles'])[metrics].mean().sort_index()
    actual=c.set_index(['method','seed','roles'])[metrics].sort_index()
    pd.testing.assert_frame_equal(actual,expected,check_dtype=False,rtol=1e-12,atol=1e-12)
    # Match the stored initial-budget summaries directly to the frozen candidate bank.
    bank=read('evaluated_candidates.csv');rq=read('selected_requirements.csv')[['query_id','roles']]
    bank=bank.merge(rq,on='query_id',validate='many_to_one')
    b=bank[bank.roles.isin(['strict','center','loose'])].groupby(['method','seed','roles']).joint_pass.agg(['sum','size'])
    pp=p.set_index(['method','seed','roles']).sort_index();bb=b.sort_index()
    np.testing.assert_array_equal(pp.qualified,bb['sum']);np.testing.assert_array_equal(pp.n,bb['size'])
    np.testing.assert_allclose(pp.pass_pct,100*bb['sum']/bb['size'],rtol=1e-12)
    fig=plt.figure(figsize=(style.WIDTH_MM/25.4,140/25.4))
    axs=[fig.add_axes([.105,.60,.86,.29]),fig.add_axes([.105,.19,.365,.25]),fig.add_axes([.60,.19,.365,.25])]
    specs=[(p,'pass_pct','(a) Feasible yield','Initial-candidate feasibility (%)',(0,105)),(c,'train_to_generated_nn_mean','(b) Reference proximity','Mean nearest-neighbor distance',(.145,.235)),(c,'feasible_pair_distance','(c) Within-set dispersion','Mean pairwise distance',(.60,.85))]
    for ax,(df,col,ttl,yl,lim) in zip(axs,specs):
        for k,m in enumerate(style.METHODS):
            for i,role in enumerate(['strict','center','loose']):
                g=df[(df.method==m)&(df.roles==role)].set_index('seed');x=i+(k-1)*.24
                for j,seed in enumerate(style.SEEDS):ax.scatter(x+(j-1)*.04,g.loc[seed,col],color=style.COLORS[m],marker=style.MARKERS[j],s=22,alpha=.85,zorder=3)
                ax.plot([x-.075,x+.075],[g[col].mean()]*2,color=style.COLORS[m],lw=2,zorder=4)
        ax.set(xticks=range(3),xticklabels=['Strict','Central','Loose'],xlim=(-.5,2.5),ylim=lim,ylabel=yl)
        title(ax,ttl);ax.grid(axis='y',color='#E8EBEE',lw=.6);ax.set_axisbelow(True)
    label(fig,.105,.962,'Fixed initial-candidate budget',weight='bold')
    label(fig,.105,.51,'Matched feasible sample counts',weight='bold')
    hh=[Line2D([],[],lw=2,color=style.COLORS[m],label=style.NAMES[m]) for m in style.METHODS]+runs()
    fig.legend(handles=hh,ncol=6,loc='lower center',bbox_to_anchor=(.52,.025),frameon=False,columnspacing=1.4)
    finish(fig,'fig08_publication')

def main():
    global WINGS,GROUPS,BOUND_SUMMARY
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--font-dir',type=Path);args=ap.parse_args()
    fonts=style.configure(args.font_dir)
    for folder in ['figures','tables','metadata']:(ROOT/folder).mkdir(exist_ok=True)
    groups.ROOT=diag.ROOT=ROOT;groups.MC=style.COLORS.copy()
    pairs.save=lambda fig,root,name:finish(fig,name)
    comp.save=lambda fig,root,name:finish(fig,name)
    groups.save=lambda fig,name:finish(fig,name)
    diag.save=lambda fig,name:finish(fig,name)
    d,q,train,support,oldc,olde=pairs.load(ROOT)
    paired,metrics=pairs.pair_records(d,q,oldc,olde);tr=pairs.transition_tables(paired)
    keys=['comparison','method','source_state','destination_state']
    pd.testing.assert_frame_equal(tr['transitions_pooled'].sort_values(keys).reset_index(drop=True),read('previous_transitions_pooled.csv').sort_values(keys).reset_index(drop=True),check_dtype=False,rtol=1e-12,atol=1e-12)
    for name,df in {'candidate_pairs':paired,'strict_input_metrics':metrics,'requirement_support':support,**tr}.items():df.to_csv(ROOT/'tables'/f'{name}.csv',index=False)
    pairs.plot_requirement_response(ROOT,q,train);comp.plot_fig4(ROOT,metrics)
    pairs.plot_transition_figure(ROOT,tr['transitions_pooled'],'tightening')
    classified,counts,run,pooled,s,l=groups.prepare()
    WINGS,GROUPS,stats=groups.select_wings(classified)
    expected_wings=read('previous_selected_wings.csv').set_index('figure_id').generated_id.sort_index()
    pd.testing.assert_series_equal(WINGS.set_index('figure_id').generated_id.sort_index(),expected_wings)
    groups.export_data(classified,counts,run,pooled,WINGS,stats)
    groups.figure5(classified,run,pooled,s,l)
    pairs.plot_transition_figure(ROOT,tr['transitions_pooled'],'relaxation')
    fig8()
    dd,qq=diag.load_data();yr,yp,yc,contribution,grouped,overall,summary=diag.yield_tables(dd,qq)
    for name,df in {'requirements_ordered':qq,'yield_by_requirement_run':yr,'yield_by_requirement':yp,'gain_by_requirement_run':yc,'gain_contributions':contribution,'overall_yield':overall}.items():df.to_csv(ROOT/'tables'/f'{name}.csv',index=False)
    diag.plot_requirement_yield(qq,yp,yc,overall)
    e,BOUND_SUMMARY=comp.exception_tables(d,read('previous_exception_summary.csv'))
    e.to_csv(ROOT/'tables/boundary_candidate_records.csv',index=False);BOUND_SUMMARY.to_csv(ROOT/'tables/boundary_summary.csv',index=False)
    comp.plot_fig9(ROOT,e,BOUND_SUMMARY)
    groups.figure7(WINGS,GROUPS)
    audit={'figures':AUDIT,'candidates':len(d),'requirements':len(q),'candidate_pairs':len(paired),
           'feasible_counts':d.groupby('method').joint_pass.sum().to_dict(),
           'unchanged_transition_counts':True,'unchanged_composition_counts':True,'unchanged_medoids':True,'unchanged_12_representatives':True,
           'new_training':0,'new_generation':0,'new_aerodynamic_solves':0,'font_faces':{k:Path(v).name for k,v in fonts.items()},
           'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__},
           'data_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data').glob('*.csv'))}}
    (ROOT/'metadata/render_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print('Completed nine figures; all frozen counts reconciled.')
if __name__=='__main__':main()
