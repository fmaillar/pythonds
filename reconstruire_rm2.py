#!/usr/bin/env python3
"""Reproduit l'édition RM2 VALIDÉE depuis les sources Git originales.

Cette édition provient de l'archive utilisateur du 21 octobre 2026 à 15:35:41.
Le programme embarque 19 fichiers .ptx modifiés et les 6 planches de tri,
plus la publication RM2. Tous les autres .ptx sont lus depuis git HEAD.
Il ne modifie JAMAIS les fichiers originaux pretext/.

Utilisation :
  python3 reconstruire_rm2.py --project ~/Documents/pythonds-rm2
  python3 reconstruire_rm2.py --project ~/Documents/pythonds-rm2 --dry-run

Si --project n’existe pas, clonage automatique du dépôt public GitHub.
Par défaut : reconstruction, compilation PDF et archive horodatée.

Le script reconstruit l'édition « connue bonne » ; il ne prétend pas résoudre
les liens Sphinx encore ambigus. Ceux-ci sont consignés dans le rapport.
"""
from __future__ import annotations
import argparse,base64,collections,datetime,hashlib,json,re,shutil,subprocess,sys,tarfile,tempfile,zlib
from pathlib import Path
from xml.etree import ElementTree as ET

PAYLOAD = (
    'c-oY^+0uf*wkG&0<xvdOrVfJ$w2Gpl3@Q#xa)C072o9hK4$t2I-Y2@dddKOAT@hXwf~?GyYkdQd@BgsU)XVlqD?NJYfBc{S<NaShr2l!3(f_m`'
    'wte>Y>E)j7)65FI^nYGm|L?5-@Y=A2wh08s+dhRLIO5?x)j=JLAS{ybNwU*+Fvq1Z)S+Mx!7!?WAr9g@)ZZUEF#aF^$N%_W1BFTI-LvqL{CBY|'
    '0wG=8CJ7HCaFW0+)U|vU^=#C)FxQ1Wr(?I<1Yz5MhhVHtA{~UJNSh$rZ3`!<e~A@)_u#*sQ|IrJI7yPYkB~k}_+H2J5RY&%A4Opl^L(d6xwwa*'
    '6xv38%Kw`Pj#xHKP_XT_|E}@>jdOd1PW0dA4ujE-gTk&yAQ(>i9Sg$|+jA)t{zvo<PEeKuyFL!v?Z3>SE@@k^PY`YQ??j7o|0Pc9ojvFOFLz`c'
    '#W06Lybfx4e`7`v`yV4GVBaNNn80nS<6|iGmq^DUDI0-1uIIocM)@#~Q{KPk?ypGB=l?DaP9Pl$b^K1p!~d4ovIy8}WA5KV`~`MU=Py4fNwt03'
    'v0>ZskPh)TD}wM4_%CrJhW;bY^<kew$NI-q{_}tN4*doGpV#d5&oF;6aMYy;(nVkjBOSv2M}=8lhrlq`!TgSoQZ|mjs005klW%w2HjcKDzfg|t'
    'quzgf|DXB%`?c;smvPn{tg~$grA}GTZfYMVhAv1Zg}61togUc)fU?>w0r&UH1P-++ue02~kodq=vA$CGU(on2LaV6{TWPgT0{7oaYK3!#Q+uA0'
    'MTlO*ZUYv^XwhDIlg4u^S>lJhXx81&d(~0vbSn0Ni7DY^^dyvPOCR<)Umw=`176M1alNdp_PZXGr;o>D5R&Dy-F+hBh;cu+Hs7e6U@8W=1<m|w'
    'k?g3g=3~KL>hC3Jy)@eitxmcIh4o;@9z1p3C*h`B9)8ln&qlTOwKLp03-dW@R5S6c{Gx-<Riya&RVLSScG|||!f2kY+x(t3Gx@o$Zu)54O&=EI'
    'JswJUX1aKNciEtukx{tS4#}bnbQAD}2WQE#7x?Al_hJU$!^FJ`>T<g4^Z1#OX!^IJ){b7AD8QEqzOuJ3zgfVNF>aKd9zJhK)a}S2GKxMv;$u(!'
    '`jbbBeI=ceCShWas2dDY6)h+tK>S2x3~8sVe9LwdVQ#j=U{W)uMqT1ky#UiQBg4oFxj%qU!3DT)2A`^ZddS!Q6<R#K-RoGzz!5udeb%#wnO3(2'
    'Q~PMm%W_@qcla&Ut?%3Ef#@c;$5O!k+iNhnY$x|ns*HSe$*ku0-F=AyC&MV^oZm6Kb9lMz`{|5W5nP+ou?RT&K_DlU(@Ycx?osalb<1=AsXAW}'
    'xp#ZtpnUGW2IBGTtUAHzF@+H2l&pw@^mU68C7tuA&~S55oMX-SeyxnI0i2CpW4$_*j;F3x=5-w7O~Aki@F{(wErlVy%YM)W7A<EcS0+$Y`s=;q'
    'ERXeVJS|@Q_|ltW_e0&HCGbX2)w`)kuqYPU!a5Cv{S!D0vd@0HIXJpYEaMt_2kYqJ<+OkKFb!r6`6_jeH~(;<Tfw28x$p6yzpkjQz87xo#jCiC'
    '?#Q8i9bS<Mm>~^1Q*==p3F~2<-7?$lsCHUdex|=7Gyj|VVyN3<@g}1WoHuq+Og$G{v}&Pt4V%iW(CwGXJbzW0UJmDSv`h1zkPgWq9ZfV3pZ~%-'
    'r{mGP;a=U&i{G)IUou{bCz#m1ZNnw1(>J*iFYVAwgX>;DjdufLvIv}4;=ZCfJL(MsR~t8^^_C_V)eL8;bN?3qvhz584bLxoE%b)gC^e$8f$F(%'
    '_L+@x2W#E%)o09lSsg780pc&;Kz_iS-Qe^R*J-#M0@UFy&5p)$q;O%L)2`W?&##%(#mJ)TplF{kb?OR?$?9Jj?$+6>9kh?V2UJU@u3j5Ar}aw}'
    'NbafHLMOuVW@W3<U<OROVFeegnCcHnt_UkBT~Wqhb+MDa6_40o=Iwbl97V!+<+%<2gD?E8wFzkS1mV1aR^8Rli0bij(706}?TqT5P^qeH!Kk13'
    'f&>frr>lCs7bo;4y>r;4VET*hlPo<tSO=Eg&)Qw-Nw1^N1pJZgzM<mt5}S`MECOfzCe^WkyFCWx>bUdN6R>GPFEXnjGtV1d{y-3)eEV~$N1S@X'
    '6?1inLGn277P#1$$E8b6>bD^Sj?k&v;}B@ly*)#-57MR^R*o0sIWb4KqTT}zTNc4I>y|a5steVM!!cjLchEDeRB`(<JwTkQ)ZntkZ}~jYZv%}0'
    'yqW7w*q#LosC|%bGrYBUE@qc9U3VJAf@w8)_S_cO^Kn$)apR_W;+AU**Aw-?7^{)jnADo9zDI@d_^L3*v@qr^|3!4LB&vgbg6W?%Lqb+3Y~QY>'
    'M|wGExA7`vZ|`6-(A-?$`eQKo&Y~mU=nBD$06#}|5zxBC$p#=i$hGYp*w?98^|<N}XlrlVygb^huyX4DUg4b^+=IRtW9Dza6;?mn^~RXmw{vyN'
    'HNxYRLa5&z7-?$h7EwPt4IYQWM!SQs#R7e$&*-J`e7&9Y^ek|rwUFN9+tgxG$z9L+=9oSvuvx|<a?)7rg7Sl7Wu?~|GnqpTW>AB#nZ?|zZ96qz'
    'U14N4W>R*I-m=#D@tzzP>eV9|rd(^YT*0~9nDe#QA>{m$eN2Yc+D>wNF?To5SqB@pYe%E(o+(J3cQ)2FN790FSYubOPI|37S?TR(>H0crCSPYT'
    '=&6KNCPzKH-mG>1BP{N9!(5Hs=vc-3!&Pg3j;<q2tuytsJN#vMo$3d*=V2YyiKWI5z_)xh$3Q>)-w~q!B?R`bJ>NkY5&~1U^cSSE0?YEX<Q|JE'
    'Y;~+qsnmC!tK?_V_;nR(6)UaB!;-dCNQ_QEqajKyvT~Yx%&hye%qF&q2EFS-=||FC5i5|DF&zpb+>H?6iyJKaJo-42=BTyjvyD9Y&EW+iFFuc|'
    'I^bUczO&#~o4CXBa5JGL@q9_&PrB;NlQa9+V^8@Rf!(%WNNN{6;Ly+*<^2>|k&f8V&liYx;QR%K3*{ilzy1&k0#npGGF|S6ta>$j-Ot^|FF~Ol'
    'Pk2DRCqUT)zs)x|OCC1TQ#k;xW|FFImtr}4H#4dJrW-i{20e^(%KNlw2`&D@Q~Sy3_cGba93jAq;XgGI{Sx$f<UY*RH!&|wo9Ew_d+~ha-Q(y!'
    '-{Fe=x_QF2z0<hqfzJ#_eWP8*r|+h*0-;gbu_G`BI`v+?a~~wrZv2t0+*$7dFW|V-%87y&x-b0BT3!InUJYcF*JHt#fwa31*Ij$LrzEgBeVSU<'
    'VienTHown(=Q3VA$Cc-ZKhS+~EruW+^D}NDM(^J=_IL7UeOeZne|)rhiZ;KDyV)Fj*P0hitNqn17k2@EAMa~V)6C+wvAE$&YTy{pM;lb8pC%*4'
    'U}bX-r)Me~HgKLmVgl{zRdq5R(7R4;>=?qe(TkHaUWT}9-FgID!7PL_+)y4a-qc$jRjt7=IbEZaZ(G$*>z7noXDRGzdAllZzh9kBmS3o*C|%JT'
    '(ydjF$tIc*#v<&J_~LorPZ{UhBNTm9I||?F;W`p#{k2!WxD-Q{RyLrobP0&(b~4x0mC?Gbk41rvwY@j0A;_z?fh6+g&C%QZCZGU$nkv(YGWwK{'
    '$BH*65WNQm#|_+8=RQzJ8(mQ4jr03s1#HL-XO(z;R*-@6)w<s>ak`bRQ@Q!zIA%SjWW5Uv5i4h=8@#;~&rVS3VrjAQ^8VCp9bam1%u(Crb6%;;'
    '>Np<K!txpT<RDchk1#^-(6EzM7=J%<z_W5fVDMUDyk5NV2Zn!ggB>DX#NZ3OAFV&-Eg(>BaT=#~FN*_yL=A^B?^M`|<qz&)c_J!VUBqX<vv7Le'
    'r^f#G0ni4<i*e@;kEeETEb^5{G4R5XjE;rfx#vuW32U{W$Dnx~P1~0%k@uH7r=wiX(rrf=y~fIA{n`_{FMOn83h16@FU!i2Z7}3=lV2<=O8e{a'
    '2Anj6%k{V0?eic3PSJU-%s%stKON0W7^|_{Suco1-Ls+kT^F33Jyti>_aYq!zv=KgqOqT3C+xeEAf3<&Ms>?IBR%_ZW?b`gan*tk%K9RCL6qfr'
    'E4M8{V*3nlPs*|R9nF*R=nA~&&-&b;=eu;3=jY4ob5mE7%DYMP^$Q42t1IByQ0G?YPNsEJHrUIxv%k|y(9@(BV`*#R)i0Cab{|=&qxb966~BKZ'
    '(P%SR&UJ2+=^?nmvzn15P>&t2X>09-JJDb{X)$htXl+Bj%;!-)?-)c0UZA;i@txW^v>X0LugquEG1lLjcx*06ZbX~_^{)`jp&u<AQJGW4YC9)2'
    'ez#7jE&>71bL|ktg5TCpKf2bP{kBd@C|T+>rr!s|_Xa$i)V}JY<1`aIwWCPBy_%|=HE8Lk2&r7HFw7K+r;an-v}*-1z$2$-hHu&1Ecdgzgglzf'
    'Yyg5?y)Qm9cZe0QXCtRmg6FHpG?$frpCx`X;?nPe^wVBPGW04xT}L(BuTEC0nLx--I>~wTI7Vyv6ga*f#uoxVkW`dpjn4Ue9Eg#Sq&<V|NyM(W'
    'YSfrgfnj#a7X8CM%Qm(B3P7k<U7m_pTB(8PucKOk)MMTQf78^xZahigW?WVf%I<VjJpTC8I`dxLHfAjil&8NDPYva;X+6IXAGJS!#B^FUeuBy`'
    'qMGea-yxgLILRp#qfW1@@O3(PU*3~@xxp1S#ry8B|Axy#-gW)ay(I6uja_!R<)|@*De80>ZBVmz=pW9{Y$2uxb|?e=NdfmB`u*DVl=`XS8haf^'
    'JFDUGIcdtAAux6M3`0+axrNxkQUhT&x$FS!up>@YLF;zzxzX1(7rQTC{>a*6+HQRPkPj;$SLx|z<nydrY|7K*)w_y(Q;0t91~11#ljXTYcGxqw'
    'yMfhTIVHC0!j7oQzk74&Uv2_uljaojxytIYU&mUmy)~_&Y#-GT_UsG__afM}{)~=DcVfjcBx%_#dDp4y+FgHvwEs{B%qJs`w<bqqCVCX%H`1?3'
    'o!!3X-j91>eSNcpikvs#u6DG9DhVwCa6Wn6cJ&-MecFOshdp6d{GwaRSDe)8O9A=a79FqGuh&f+=73svs+&AiolZJ6)Pq1B;z+%r2L5>qUEn%Y'
    'DF~$4Tj=0Q9()LY3kqbd67;7!!>cj84cnIdL#y|%(yC>5`C2}SZ5aN-N$>{b^WShrvuUt2>VYv|7E|B1fvc}qvGUYKZk5_Avok#Env<UD59~j&'
    'S>?vZdPXy%)`hB-5cw=l(dIz3hV{z!;1osq_;sI)_cB{twTo8ITdkolCRHtvGx1Gdq*i(gwx(=$33Q?DdX@O@*kkwHh>mY7X_RK%YTPUJB~l&;'
    'jsV$xPGtIW&{xDvMX~PftQ{O5-dwqLF<JGR=X%*C{JXBj!k$?iE}9Rmr%{J$w(9)Wy~cOhZyI<vi4AnpxNB!%z6HeC?o_sAcjX~`z;*@w3UxjB'
    'rSA7L{QX;<aE2RXQ9s%+qxjQ7yJGdvOYZ|yUpK!DIf82KLE?CanOY;)JEu-<u!(T+qf*>b++hbLt1?yK?@5+4_JEeq<<I-$nW~t-XN)t><mThM'
    '-f}tg_E-%5k>K=`2jUx4#NZ?B<W0-D%|Omcem$`KV~)XZY&6)vCLKua&!ewqWB%9E^(oj@Qi=}m8?-ag+LF*%<x{U|we1izlg47g*wX2)DfzZ&'
    'JZ|;dlLjlzbIqS04hUaekc~~QKRV>{P@z<a%kTVSLvA)x>XLVY@IK$JUvaE*ju)wp@+YveXO>iK&RF6vnw_6)vwcu~`*RsSVu=HnBjoueK?7EQ'
    'Qr!11eP#$%2Bog~R_yNlW3XWmP|QSAZm;fohz#D+Wlq5f;ey4NfvdO5u3A|ZB0N*}lF7xUIvNDK+u>YSQ?A{_Dns06ijK5mN6mSp&aTsMHYc`Y'
    '6v2o1>2g_rdyk@NMQU?HN}VEHTKbE*cTRfs(jpVDUdgttZ=_&JbB~?cY~oRHHJJeWJEXQgl}Gcvfcb_{JA>Qmvsl{}Tl7=noS2lg>eQF`efZ60'
    'MX(5kS-E82z1NgXzb@R=C)T)@>Cil<Lk2_^pQ)QlpGtQzn05NmxU!iwZs*N<`d+tHU@A^W=C3|xpu7E|#;rjJS>`>``)&>%iS9HeG$^KJ=F@y0'
    'iv|ZtYyMTYT7JIWZV}?psqMmXV<x6qW7)FSQB!^OC!dbP^0U>alv1o&00*HTk1M0$!fo!?86uN!gBo-i>V0X4?%W(li_5lL?CmKErJFMcBM5_e'
    'm+gG>YDBk0Vt^3QCl&8_8k@R$KA_q|<Hqxn2H1Y--Qq`$H|^T}NB%}kXLkio$fPNS;-JzDwl<fah88?2)_qHt=<ThevQMqX=Famt&u{u=pgtfI'
    '{|?8%3Z>uLt8rlD;9Co4*RO@lgl_R_$PbcVZNPezFZA=#99C)z`BR_P6n?Ei$`0HQ&ZD^%B(c33v_?<IBA$ZK7%?a(<}ZJGzHaya{x9*-OHI5T'
    't{rdlM$9V1_Ia;K_-Z4#cSw^Pc4~5hYiAW`vd!Zsu(c;~cbt}vi9evcQ(lQRd=^B6864vMuceIPx6u<$F=}y38pFWc3jHTKEu8uOeu5}hdP*N`'
    'AJ-rCeY~!~`RsFW8o`H{E#~pQI90CNNvumPxWGKH(@H;N?yf;g+ZEE>sg%m*+T?ppd;!s^t<L8rQaxOfMf|MI!22X;x779fn6BvQ`P=@3g0;V8'
    'tprO2^H|GzeA-A1ax>zq$+@|Cn8$|o>bWDmIyx*_<bLLXa4An77n?+MMPD58z%lE^pn4>BwXs~rEv8qm5euo;&gR;C7|i&q46Ex<mr^zn53)>5'
    'TR(UMhs$l!z8)TplW3yR-vWy3?)_c<H7)SqNGUf&V2v+;nfiw^%hlyVA7O6RG%oJ}Q1r0nL>ljIHLP$0iJJX1Nm6Zj%~f{FgX!G|>*}NSeiHiT'
    'PiF*pR=>i-{B4?Vb_y&E(*IB@XHFyL3%(C4%4o8ikF<Ai7%RQ;T*@+a(6c!9rx@g0Yc|%M_N>&=bkGp#fA<;AKjlCTyz{}I9C%0maB`{dJ~RJ&'
    'AyRbC>i$lPozSmL4P0!gD_Gq$iOf^+3uC4;*H#ubH_O}R(S@|DS-D9vQOdt;`w_t5=(KL*y8sJ{TaUM;zUXX*@6$d-QI~eL7J4Svn-3*6x7Ozy'
    'J}%@1S#%CaZ}82f3VK~ZBgTa4kA5Uow-*XnzK#!fx0rw5{mRf3k66nwj;nY;bQ@=(+;d0>M@}#h?hgSt>d}gm^5JeF-iK;eLbO${dpv!`MBHlU'
    'mir<3I?FEbPJ1uwYaq^DQmO9f#2_v`snWkzPdSpP2;0>l4VewV(RwUIYP3>=4+bm3sygcNZj0WEH%gp1wJ1<k4+EMi?LArWF`GL6gF;hbPgztl'
    '_xPMYU*wnxCKZhPr4?dMS-6C_!&B|Mc@N(D$;OMXHWdx!vkvInxh^jl3waHlK)z~tVJrqJoJ5~yXb;^U^sSufC4N4s@`E@$gK7!dlJKI1^OM)D'
    '4Y3jaydaZOLL79EQFqrfyjS(Ljr}`1(dE4x_Q<(t8l5)R8}jRF8|hDv_WZ<9?~!$Gw-l}IZ6<Y<vsL;+((Tjn=U1_A+yi#c`V;0!nCa3`nf%7+'
    'w%ZEe@1Yo{;N$BGDLJ}ZyRh(Z9w(v^rgq!6*3GK+`Bijo`BWcZK|Oqof7hFCUkSzE*H03~{N=1S-c}hy2C4mR-JVnGmE}?<ntb>m1wY#HPw-lW'
    'Z~#cVzWa`KPCg8e+&X5v-C#F^vw5F{GkCJbz;8<L4g%3_QLlGXMBfNc6>izRMipd!JGZYP<!(!)+TXQi&Xn_a7C$h~FKKJ_sMjnw$_~~XzF8c8'
    'S>vE`iXp*oYUB)GwP#@Wex&m?Ke>g6LvKK<l`2?;f&RW$Dcg%yAJvVzwKB&6CtTVcXU3IVgqqX}uEZ{R6s-)e*l#-EdV^WB+imGl5BuF3!E^fY'
    '?w@z8)A*i+TR(<}hXFCupI58x=Zp9=!Pj1&M#eJ#T(4*)%fQ!Tpl6mcZz73uA9i@|VvK(0i3@zEcV|Y9fT^}$a6WG6mAZ9Iy00p#$tGK+I{LjB'
    'wXWx7deVB=3Q*4`g~XzU5-)zWp4d^R=ZR$4rY#<{Cpr2<03trkUA~wj!WEhw9wP$q_XB|yTbL`z2YVMP(}&Fj7F`O&fTycdlp1D{(eHdJz9dm&'
    '^S+w5?1-<xrkIZB=&8SA0QFt(HMLU69Py8+sLuDU^@`xOL5u}E4^j73nO0{Qf#+hYA~^jNGxhiq)y5Ll3y~FD*%OC-Bgu5z<HPUbk~X>LCL?;S'
    '5B&Jj>3v3m^Dp|`Az7E4)Ot7>K@t1d2!2gnnx6rGX+9e|_o*e7LpiYic=CL{uJ@-lDoInRt`L?DJ;XBf%J!B#4CVS;{GISU15CKtLDk0O)m#ya'
    'UG2N<sovo>$I4EKZEsvYSAE<bXXYg$Wc)R)L0nOP&gcSBE=#Q5&W_w+e5eyj9pI=fS}chN5ORls9J$?ItPErBD1ASVZB7ZumW9-aQdbN!(XnW{'
    'UyJ1#I#F9A71<hsRRoav6ORp9!JFSgKHNd}n6vVc8L5Xrk>e@X&JTZz`R9^$LbSkRH<k75&H+E^2?P0B&nl>KP7!D7t^i1WTJGgC(9vv?O}OQW'
    'uKQYlj4VF}BRjGjk34GA%{LXt;1)|Axj*l1z<3<&{*8<-3Idud0I-6`>o@yy#(h;kO<U7xck3LmH56%!t9&^czr?zp^yMq}j$vn64`;G7Jf~Z5'
    'dV4glnYXcWaa68IKQ`G8p3uwjR-2BDr+b@mNtGw#h-kZN9iEeuk}c_F20nn_(}`+_3bd;VOPJ<=(WrX(R;PC;?O#i%du?(Xpj7v(?rEsK`TSLF'
    '70vl(Y*wC#7*wlMDd&ogb{I{|-JpGGkGf)py!MkpyFaMe!dn!6<{*C_b}w+#xpIiN4!G*RJsUsbFV5_er&UhDfp*G^HT9Zn0m*{gTieKFEoupt'
    'rU?G#Q~QFlIn!Jp86iWUs8w-3v}5^fYk#;n%%}!4J20W8Wo{8xtK8NXFKNLBi2J>YplpmOdsJryvm9v9d!Nwivg*l$7Zr7s#qA{?8?KnM;I?jG'
    'f%*8XIDba4rYeWuZ(IEnPJ@{o*w_oCt4DQ<jGmy;_}_Wg;$I#QtgnMXf7jn7U*^-2jT*aer-8Frg5kM1GXH!};FYDm*65Qz^8UF!z@nYs7bkY1'
    '-@8p?OG?)%#jXs!`s?=3Cum>bsPlSzS2=}^CTeVwH_{l@yVuvZ_Ic@+nR_q&^HxBL){b+&{R56CeX&2;{DE6?;TDp-PF9dW2M18Fw>07Ver#ob'
    'HgtnH#~*Fh*0Z)$V;*v&xe4R;mL9*HseU7rQ!6Gh2V@7yH%_j_(nl6%xEUQI={mZ<Wc-(HLS$Ee-=vWFuvFX&<mpCdz=_x@M+{59e$LY22J*d2'
    'k^YRn+8CFNsvGxq=6c&w8Q8*n7$4`()I{0y;a)te><t?|XD{-E!|6MDLfEA?>1sLLv~?Wpd!OcSphT<4_Qy4qS{1KP&47JmNZpC^#-GlBW0XAd'
    'rWt(yEbHaRfuQB7er=g<S6&OfX7%@R30uvT$oI@pppoyy9`*-|a?#*zWIouSloFNI3)-nym3ynE|H%ceSk__2a|P<pmJEcZC(xB00GO-VZDupo'
    ')1@)N51%7{>^9m?Z}kUR?d!nYtNj~xu!BV(`WcV>)qq9ZH_LQ|>qOSy5y{`+$?+~PlhLAWeqCJMD)cn4Gh?dbOVF-1^lt5JtZ%sFygA`o4!>o@'
    'R5fhOWalNfFOhL|t)A;28T~+X|B<{(vAd=jzQ9hk*X-K5B)HB039OubH@l!zPWInpGG=(%bkDwv9NVrJKXr5=Kf6zlZ;jkBC0i*;`^KbDZ^F=q'
    'WBNT)b(aB5#<^-F4mRbuDSxF^^H}M{txEfW8pY(WNvB&Z-a_R0rkp*y+PrAnm!tO$_8lESQPvvek@nL2=(r7o2>Z>|hT%><SS|L2!#(s`o7W{G'
    '0ZZ}Lrgug;YLIwGJhwMb3=L^tNsea&<N0wz?%&aKea0Lzcmu{YJn`}B6XJQnwvS&nyo0}S@-Vs#Fc5?y*klC_2#@{Ucnpl6Q~<S+%Hz3FpZr<x'
    'c@^Lv9e~vges)8J`+2=zf6FCvx>Sg5IW~dg;CV=0f7XJx>z^~eJU>8)?rPh94V|dp0vpgpYtpfe%aiC<DImnYpfGcVk=~v1{?*PN#z9u*t6-KA'
    'Gf7qqgr7zkwS($T3UK>tVnoGagtzw1a%mbO@<)NMB)|kTQFEj_K!k;WT<%w@0NcG+*XcB|QTF(g35mi=&qtaR-9~szCXKZuj`{I1%!*B7Jnm{L'
    '@T`)rgUw`E1NPOS_(wfgLFq%gwf4>z=k;N8go+zO9ZyM6y3TRJi3!c0$SiV+T16DIyhvLnLh+DuaJA8Ob5CF~;!OHF`t}C6rm}VC>$x9JLG7Rx'
    '=C>_>{N2P?7aphiceEp&;}%4#pJ#QoayJ=!Ki!Y>{zw(O9r<lg%JJiURPbyAo^p70n;<f5hCA4WdY|F3-?zish2qpo|27@}nhQjjvjjSWP-5FW'
    'U&4L!y6#!HJOhGahtwhNe#4*7<_v%;w{BZ(CDMCz;_&W(_CwFH;QZ{))0%t2<iiPmSPQIbg3r_HabfN6VkcL&Y|S4(+>|jag`O=yu|FI#*779n'
    'Sg@gAuPdNCrF8aTkl72mQa$-$=)~*@(C=L7ol-i5#+K7RMt6Nvd``E)2pWj9Th}mhT=D8kBfB*h#-N<G+Ct^j<F{=(Z|v)j`xs6_sPPK?MP7dX'
    '0f@U%9|VS2EX?%34h+!(s`8KmOgzoJVN8Dw8vHcVvb9&wzKwiIE!tMPGJWawe#u0Y6RWlUL0c?Z&Y$ShW3f-(q|1RwZ?Ef2Z7k6SYQ)Ebk?zbf'
    'SpiGHA8?WMY`eLgwxnja!E&dE-FUH?P6SM=uWhadfKNw>*fW`h)?Q}gL%{F8LchMz_E56+*MHCtNI3r3bl1NGr<Y~@_j4PIcGlziQfv6@lhAnX'
    'M$zr+AC}#A(X6wFY>dHv?xCcvBoI0K#JfW7LGb+giS{QkUE(vbj_C3Ha4NM*X}(TSqhB_y?AUZ3eoXI^v@SEpC3={dMFS0^pVHw;X15JT5_4U5'
    'Kw^8fyJYYoz*A$?Uun`zpLB-jmO@?I^yxAw4s3h9-&9TDeVSFNoh^+nhbDbJcE(kJQ{Ztu5*8CEHIL!_bDT+YLq|q$=HGn_^8Z!<+4!Fd;OVN|'
    'e!HFxyEwS<eWa$1?@N{mvUsT~n`z@QHwJ(^-mf?wj0GI19e7)uw=_#=S>B)yZ00|n^GA&KVc&<?slDH){<oP%jJRKf$sf1)paU;<eJQ&(FV_R!'
    'i&x-ee%@|ukC0)k^JuMU>%ghgv4_rv+q=T3qLpBq?I_gG`i>p;*xgFl`cM;-Qw-%kYyJhlx;|@2g|vrf(S8DLm5}$pxgd4n(I1q_?Tso9YnM)E'
    'tZh31JYRKtCXbrfm+n-R8b3xCTLD_SQLZePcD;VCEZuGExDGR{tP<Wj+MNYuF)R8ZN$uhrJ6Y0TXS7=uyC(}8hz)FS{wV-j5Cr};;I4g4O#2SL'
    'B&trojIsjG7jr7ZO!d>*I4sjoj)y@j7!9MteDs8t+en7&-WwJx&)VV75#neYwEq12@}x}ywn5+NWZAtQLw*hsrXs@p9BFs$-&G9Ns<Vop*Au4t'
    'jZ^h!!O6KYM>T)_)d%o*Z|LXlbXPqBi?EelpU3Kz4$0Y{MsK)_+5TI?c|-ceN$WSn7W#Hay^ZWTyLkKO9%p5edR#bie;0SPJ~2AJu1@|~A#!|p'
    'O_E1}q;KaufezyNcPOSprO(_uaJYQDPa71JYB&4`PcQY#H|P2fQyn$eNhfzN5<Navk`TY&8KDGhEHITWV|fqJ9UFCxh+H&lIn{RN^TjVBz&GRu'
    'wtL?57x)tstHboPy+m#Q1LSARgu(Nes1jxmMe{#_O>Yo-&D=`O9`vdTwme)9tKZ_Q&+7&-dAliPJk)ArTy|S}TFkpa!ZsS8&MLG|F)CROOnw{3'
    ')2O^iTV48tiZ!2J&6grK&^a=t>1BV+!O8Yz$J4+CHx4g~GwZ@Nk2F_#vuU=`o&DgC&(X=dPkg0Ut%#<{F?ZhOlniE0Pe0a$jaSw&R=*6D+l|*}'
    'hfg^cKEFZ9AL`f6seI(JFzg=dwd0Da7JSQ-c0zAjqv|_;C4N>lTVYyQuXlX%*MlLwAbDKDMERVU&&yq7`$9Qq>XU_OHqKAIaDZkeTzXY(W7YF@'
    'CG8Pl<+cnqd8LSUR-0did_UgyF90``oxXJ*9myDZRE`iiXqCIAzZB{WjsVbiiNJ^3`7p-X0wZ(UW_e3W<|KvvZcNnvGzT|@)o!gh^PW@`7*VnT'
    '>*Dsv)M3m0EdH3ATWf*pQ(<Vu8#WWyInutJ?kqU=$M3=JSP>qV-aDCq7z}R|n7JUVj2{bG7YOYIu;oNLtZQY7cF|X_G*8<J?$o<mjadxA$7{Ci'
    '0+nK`UN}bMP0iDls=4_t@_Bu7Q*U`?DM_ex?hm@dS?nM3fr~#a#$GIy$!{@VqLX&lWA<d@o$$Y-dHAYlq~Eh4QTt%{76-p8p6l%88anOvTCK10'
    '(Axf~cdZPAYTW<*XtFP?CneCei>cqX(AUV^b97o1N9vX~I_vq!44Ojs>-3(!oPI~s3D^pd`{AOhXsc-DdutOK*9oL7weF?AHNm2I1BObB9#dJ)'
    'TT}e6*#-q*sf)P7lF0AHkF*zYM-%rx95+|pZ_{vEM>E5ee71kBxi?yPwp4G=t{?VG7yA2YuSZ<5gC61zG}h*@K4wZQru+Btq3Z7V?eC?T#f#R?'
    'rBrdt4|Q%$8W-jl_urw9u@(beErnkP6GzPFN&Z_s%H=v2HX}nC);AM7GLe3Bqb@>YbD^8b#Uyg?eLvjk3P)P6MESj)?fUj-R9E-YblASU$Jl<l'
    'jZ<#kPLs+xcn@!*6;whhbV?|p<xYrgW!{zR$L{qOLQ|<XSrk-cbyr8blV(lYr?Ebd%I*8JvE6~aPRj+y_0`CfV)C#ayjr$hHFb4zQ@E|WjghVH'
    'n05Yj?beP;ule{6)%*L!Ih_sX3cNx;TT{7=tD-&4+~XX4AyYAg^|bS|3#{7OrJOKa23UFx>+PF+M77$>IiOWn?_~;jxw7p|Z#%3$KleN-=Tmme'
    '#((a}y*IZN8vMY}Y1r*yc1Jj-oz9toE<i$6PrYiz<Iu*iP4^PGbsP7zvTtKL2YdW+)+{k+s(MMWzO==VIqS^fNM9;HXS&nE)c?+(<ZA&rYrZXQ'
    '?L+AGRV{C+K%z_!!CE|?ANY34b4s=vFWe!vil?jP*kr}9J!!=M<|YLPiYEua_-?s2@vS9WZwN4xWv<;PpZ#@kJR)l*XpAu6QLW|$keBD(*(_wy'
    '{IMnPt}?<Ex!r=pY9}_V2XC~EbpFczNlfIa%hgqyL&UqBk6y3tbP%-o<1PfacS1$SB@PJ+?tUe0n&PM_{ucKRu1*v*$cb~{owJ#rar4V2xI=?<'
    '@K9h4d%O*Qve|yo#AA~Pk9Ps_2VD$wsHgO#jwY{-){f0KdK`b}Y8N19mjxBA^-VyN2PErU>t;tSYn#;|coN@Zkj%UF_oZ{b_{()|T$zjGloX+S'
    'Ti#R-C6=}KQpVr+4HJ&XYXJ<ao$Y=(WlxuJ$r^U3%x!}GV@Pw<QprEBdL_HTy0yDqYT+Aag6~&tb*%5RT8s^%Ue)Y+;*MoLEwR|*B%xUqK3%?a'
    'j6;3#6)Nh<@>g{&7MR^>!pzuejU7Hev*+tfC#h4c&U5io%#JxG1e$ci%WL&;Zd%bb%9`#Un`@i~+O49Izu(YEku+Q@alE}JwmJOIJtUW>cRyRj'
    'f9)b++^3Z|p8KDZ@Sit_tb6FC8}AvWVdlC2Z&}<Ue;~I+H!{yGc`Sk7q%r|2&1W`=n=_kea^XadAHwwZjCq{S%dpY^-foC7>Qek}R;?+l1HRkT'
    'x)4s!k>SJ0*(P^R9rcqA^I6<;%HIl=?AxJZ2`DB<RobRoe$(0=z2nNId$V|Y16Fin{UNkHm9^UgdtJVu^XH-L`@E@C*T3wsZ(?jbUb4jvBP)-|'
    'VShil)Mlz_%OCDE><&J=8^XwsrmxX)J;ME4c}~TN0&K_Qr<{!j`zad&Ha~iP633-G%i-y-mT~BV<|}ikf!g(beI57VvsU(Y>y(r^N>)aTqqxqt'
    '({(X@cQx=5TuHa}-BafL7Y4nwGb7A~cWuh1qxW72!?S9;npJM^aHihnHuJ3am+N>pKQ!@2=<SDO>NXS|x=0ROtMsqPwMvu&LpMr4Yb34PR<7J7'
    'FRObteS4N)K#mA=lzsf^T#++t^uqd+^RfBYwwvmr-tZ;b_@3{z-N88QNo@pl;j~w9@}BCEK4<;eG8C=nD={E#ZK(%sg9&qaKV2A_tKQI40`rY='
    'P075SYMWGJu)q-$i?^{l3jfx_0N9rNngSI^31fqKv~b~}z0%)3`)iMcrEl{S_t95XvM_&Ra~Y#t$Nz9N!cCNWf=qgC?IOo?PG<2z(l8eUmU0cg'
    'n{~mFhI79TldImSVuO9QO;K83U&^FMsItBQ`({&jBT!yQqxRQqr_n9>fhPu=Uu6`itnMCJKJE$m%p;m>=Q9zT*{V1TK0UJ89vX?#OxaFYsL`nP'
    '{5e?vL(VmVau`JBXUmmXSzLL%$}_Fk+Sjx8Iy0?Jk}LlG_~`WCz0-4Yuy)8K%{ny<Vf?qgrO8Gzc*irg?AMy(um*D^B0sJ7yUG<v3)%J7!mB+?'
    'TOzlw@Y?1eFK?aAXf}EWGuLh!D|xQ|odbnNFS-fO))~s?azPi9bO(BQ(AzCG;+8m9;QW_*`tuUa8&kv4bO_e$%%~V{tA1hvEfVK7GhGD6raw+2'
    'iJ{He*#VnCaFOW)y<fr*I%BA){#Rs&to#nXwz^wVq`*cVQA1X@U-Lac&^J-PzNZ8d1}3NVf9Ux4G%rOHoJ=>-`|)O1=11;x+oN-=M;0!@BiEbI'
    '*@H^Wzm|c9^{GAryBPVK8s57ymd6cY!+xbu_{?&O+(4)oXtA9RI==XhHB}$9n>%OL5g9spe`b&8?e3lE-+)?Y4xfdUKLdD)wOD$+8`8!ixKS{-'
    '?pV{e)`~=_VSTgsEo8KH8y5SA_k^kjT+xraWH6~blsQ>Byu4J+C4CKS2RntI&$N7{Rw?(rJ&fXhs3rZ_8YHbJIR7NDx*wwJKQs1KVXR^bpU!1-'
    '>a^Pnahzb6wijK>bUFcwR<mP2RAX_Sjv;=Xff7I+{-jWehRx=Bkd3BMZ32XEFnvAfE;E%+!=*EeOGLRGmNQnU(tCR^RC?P;7r7QLTI(Px=JG|d'
    '<>%-INY`}AO4n);-#MunKkJL-6Pvo_6Zq8mRMkm@fNHyBaj9+hqV%T*`Ns74$9&!5&mZc`pP$x<iPqt$G)EtWqx>PK7D}M6jx%bwvl7vUQp>k;'
    'gJD-aylbK7vHm!;78Me3_;zr0NA%}le!oJl92{Y_Wya_>rFDd_Qo?u>5z!gb!aor`)C(qSR}!j%&AQ@tMn7JQKR-4`I}^}E$mM&|pGD!_ZxE;b'
    'VTwW*?j)NuFDEZIYsQzWSo?IRu6W-K*7%<zI0NwrZ7k~r;P?7ek^c4R2?9HLec@x*P34dtFtrox+9P~7SPforYd#8|hke=^HkYGJMCZhgEFMDn'
    's{JaznSP9v_l-nnmqhSK{=#B@Ma-wm%L_A?E)M#6FbS+%&oEIy&z|iq{&lcDy&HxKx@}p`FN#yBuhqw&3b%HLxyTSflI}VUWTQ>b<+u5~4hv?T'
    '2Df^|HXe&c3ENeB%7=})(5+o=5f@wrx1yR=g&x~CsO<vWaHLP;+hj!}mHj!DbdRfP?3>xQH#2Qg=@4`)oM>e<9F9&b9W;7tpSpG)vk|k@#biBe'
    '(UPx5yXXKGpt7Y7;$!SKr#@FG6>5Wi7TKdAw>L|!SL(rO`l5PEbad^s4vR4tG*r|bLDcQFANC50eq0&XGnE~x3BhWrP2Ih{tSpEzUTGOiH#(KI'
    '3@%H?GmhQ_agB1JcORV8IC%>Dn=fTvx(MgA9W8zRyds)Ywtbcdi)~FmBGvboJ@zwy65MOrV!-)I@7?Vu?Z%w$EhA0<l#$a_|KQ<FRPUn(n(IpZ'
    '+})*4bG-%^H*6KjZ%^H|$Q+Q%%9Keu-y02w4{T}^u(^6~>bpn!QYVbNybj?Dsmd@We$T<7PBwq7nj<SQ$f~?HTYj>(@T>K|@tpCYx7<%ZJmzl0'
    '-JkD0*T7T3T@R!*g}b-uFUWYTzudFz!TAZXm{j*|b0|LVX{XkSYwu5U-vl<|F+uxFdJNnhb>8McO-iWOhRO=gMZ_Gl1{)K7_9{;ZdsID18WoE_'
    '{`9}aQLly{CHJwS2ek(|bcCNNJ!LfDgR1+1E-JZhTl~V`VaL{Icx{DJR790=7i4b9=SuWH`Zh#N^!0A{ac?ryhUlho*bc5&hn^q&^HML6N%dZl'
    'mnun*=AY6pSzCttgPE_N*vN-?YV&=8mvWn<1#RZDF7$BOV`wYtB_Ey0Ew?!y7lgYaH?^A_LS1gCz<pp_>AqIe9lB_^;<~cs@9#WgoOu%<hx)uH'
    'LJtJ4D7OK6^NdAp<yw_iFWCR`CPwKH@)3FnbTTzybk?BSpQov;h>B6~wU>BJI?i|PKgwqbw+mgcYv~b+<z<`6#;Lrnb>ZU!U1YP^->Q>0L^AP='
    'p7EW+Sc-Ake7~aca*Q-h^GBAoX@|2n&&#$39*3jP*lzIT{mwG0C{Jq|?Gf{DxA>+n8A=D~ZsHT4zHtfMmbU8r?h>{!-X2pu_Ky=@U%=jcF;VI@'
    'ea14A@8<$9CI!6*DWS8UG2JTW($jiC7jU#)e5O#plVYuXw!dzaf9yVqn#K}+b+u;e*j35%yaE*uZ2_=fMU<@Y%Dxd<;nB3M?*!;V%!T*(2>wo='
    'U032?ifhattiCJ$K7K%zxx-J?p|1Cy;`zOql=@-^9){iF@D{krcIm+OLqsq#e^cTdzb<E+?TC5Y&QD;V?!s;Jjs@+Mm|u<ju!(!dDUR4;IK$>8'
    'aL`;rfvVfR?%(;>lFg^HQ)LBEGuhU`&^-^!Y0beq-e4X@mb$1ccB?gIuU@TNy`Qy~+O~g&AGfgdw9iFJL>g?IFTqEB;kDR9wDNfj>T9Zy7E}(o'
    '{9wdSC@+?|?fMr|?9_ea++`p-YnNZe_gR~7JH#J*y(OncUGU{-bUJ`|v86W6#k;x~WplXR-wcPaIgqJ8pXbf4$=sf<EbQF){#gUkZH~7yN>iXZ'
    'QcIf^dKEVP$rJy;^<$O3072P`iE3?2U~eivyq?3T)g51?*Qw;e?jH<}CrmhMe|V)m+=188FQ^#_vzXt5^n--@DIw*Dktt7Gb=C;|qU%0H9)H4f'
    'xdrU~Xg?j{aPgzMbZ3^g@0xvLR>K!+@5K*GYGN?3;xh#aXrrdRn&_H*-4@;k&B>{Syw(z255<#x@)qTcSoA-Z!I`JqZ^;2e{d+U>kiuN)v^JYb'
    'ZzmS_!E|83yWdBU1_9|Z==<65p{O=PuYhFq8d>jnTn{JqK7PErEq-ec%DCbGZe=JhUX5ApzS*+BS*@(k|1UPqbZ1#$OQY991fv)e0mpz7$e=O^'
    '3J5<?8~_IfWe`EV_I|%kx|5Tf8xX75`>C};RZRxm+>X%mdH1A)=*Zk!qp;J*{Oo=hIlY#a3|jLHnuy;g=eb?q`Axn?bvyEJB!B#Iab{HWX#-N`'
    '{drJ(YWN*%cVyLN<prwlv(yiFNOM#!atQ&~jT<wXb<rkVno`!?Pa+So&XWbkJ)1Rj5M2Dvoa0Lc_zszaR+(${pst<X(Jrt&4W9T(`s~I7{xx{a'
    'v3g#A?tJ%mb$>>C2jn*m;in|#OPLxR+WKg@0StVv6!5Hma~r|7oO{&$h-l0EvZs*WoWrjayz7|~PE9C$h9cJ~(KYt`6hHr&KIo)4dF!373PF9F'
    '&wE;M@}4361l@c$_03G4caglO-r4u|aWyDsuI!g`uM+RfvhCKh6Nqt9;%;6*pBO{-nId^bvNhyVUiHWBl9c#txR|aFUe28OMhBRE_6UHZ&0b&l'
    'TzG9Gvy?QvGUVhPh1b!;@}b6GX{G|~UO8u-sW4>2K&b(aJdbzH>h*kR;l<;r?r9<X!_N_THf{^a0k++rdHYy{83m|R$?__12Hdm4zrnsRR=Ilg'
    'y=1gwp>AFsN$y!Tn<>s>cMH8bjgb+&ApZ|8upU{#n_c)QJTbHU<M!r+{v9FDw@<=2Mt_Mo00v-RsWwlZnKeRaGR5~tE>5UMwDX_V;nJ*?_XEW4'
    'L)u?@egDc)OjL$n1G$`8nko3vNMmu&K=0^f-6(B>thdjfeSLm;Nvt;<AXDtm`hK-yj48}2S#z?xzNs^K#_eh_C~gZVSU!7@-3EH>Mm;x-r@OR^'
    '3&E`Mj$H}M{ebc-o2j9_Ge%z64k@+g;jH3Gb92hWlO|1_COt%o>_6=j%}#wZHhVe!<l1a8v=`qh{%heZE`9ZFr)-vA#H4D77muaqRJS>pKZN`9'
    '${x!X5%u*5?Uf8Hx-?8^jf!*)?g*xWF7*8j<`89`|Af+9SotjX>O9yYtJg|RFjeJEeZ#4L#1%s1)j?iR)_i$OPJ^Fr@2wW7cPV?^p0qCh=(Zth'
    '_jR^|0qQtU!|t~w;dA+P<Yry7o%cSE>uf~Ipz<?Lcs}k4#46k)Rguv3;T=<O4SH@8x!J!0=b5L@x_?X<WSM!Pu4%(TJ4js`MkqN)Tpa@q)y;=S'
    'igd+J(QeYl=W;Z*@o_EQ?&x;EC61Du?diTZ2P)w!i_znm!*SA&{ehTWY1JrO$@CQiM|&|@_#EU?!~yL(s7is^{V5r;-Cg~;qg1W;+QnrZ<br4^'
    '6ozl3rpBVH$2uLPFIlvI<75c_Ac4*?IB8cq@ro9$Z`1DL%}vWy%|BZbVrv$To%^}-MLLS|*9pZ>xm-upM=7Zg*X~q5nD}Ol`l^`fV`0|4+1CZ5'
    'f2rsot=0V6Fy4`p46#GvcEasFeN0Ykb9w9OF3~yHty&AmvX|^kyQPy1K(YGbCR?iKb~}G<bUG-gIJXZuJcV0(IU9rF+N~lCe1wqm41;f%U}$3f'
    'RK^E=IMrA5pOmy}*V=IPM1q}nkcC3H?)qsRylL#Ed7IxhOS1JY#8|tvc=R`x`2KR&m43Hx4OCae&{mX53dX-Vm}t(_NP(q~NNy3PIk%wnS{XJw'
    'I&$5|@+=C9<#H`Q`wbqOd-HMiu&4{gL|#*yZe1tN5~9Q#Rm0c&Fc*8kvl2fBR}r2KqD>e~I!XR}kg7T$i%l~{{g(2ki|*k(7|<V`>a>P`kJr!T'
    '%L0xKKzUdGkT}(9Km)CI+N1Eg-qI`jxID5jHa={&e*l8njy44gTkv2)p6Vxid%JZje*38Ux9wKWu15tvfP`z=&Cz181W$s+PEPFr9eLpRxTIjo'
    '#JTRohp5Oj(6?c{?<v};X>LmVt<;ZUv}5k)<S=~Hc9F<zsOtrh&b4?ruLyylN|zRTMSmlh4oD&M-+Ec@JAroGOIOU$r{M#dSn`V-oS{=q{?bX;'
    'KRP}HyYLD5cfK*Ya;aPQP1xzz?K(K$o$YB;vG2+=nRXzOPDO9lM(fL{GHDSFzpf2h1ke@c@%Q(u+%IQHxg^%_->1dS@xxEJl-7p6uj1ZlcMVQs'
    '?Y;vx>q0n^LE6o#ogxZda})RR)9c;rZSZY&o`qXrtWPI9@Lzg&zs77tgt?q^Hununz%<XQAR(`{WX@dTvz70u3QijZ71utZJ9CJ|xRj?GxH$Q5'
    '6rM6x1qkm|ipq%<970WO{x=hQK1JWk-*~~gb-#7X^6u=$;BMTzrdBJp%kdEfR*ylOwklq}z8?flZuc}*scT6Wv90V8S57&Hf=zOW40n6VxLT*d'
    'Qk&!J{#rO}4n3)Tr|HT!_(e-CXNc+>>DAu%D;BSfn+SID--vs@pTJsCo={P~p84}t?5f!4G&SwO&e>!Z1jjcX-=_6uGk^CfN4x6@sZ46-+CO~U'
    'Zaog110PPazih`mpm>l^sP8J&Q~xyt;=V^ni7r;8IgtPu__tO2ZZZ1`bDC6Imyo`{Dd;DrpLM&itMqNT+!V|^pDyn=*g08?bS1vThNlQ4*hv@D'
    'etWZ}*Y7%CWi><DS%sg_U=INN+9#@(L9H05-6uwD;w6Yb0Zt;wgLv1OVFRfXbSq@KudH7Mrxd#TOxN~TmkVQfotE2cdu{lQd?9MtX6VbigYtYx'
    'RD~EEgx=Cq39j!iXXD<mU*W3yU@MVEXTa3Q0mR+6cYA)vO_8Y$JFI<u?e*$$ZPC!BT(QYtb~zV#dD*VG`9t@M>3Zx~caM@Ghrc<q+UjM$!q#Fm'
    'vP|c>t#yt^78TD40-vv@zs6kKz+=6ey5rLy?~hj3jX%7dQKq3@!I~I0_rEPsR|d#4sc;Ps9e!i+{5V9it)$HpRSXl6DK62<{EQzR0txtXjei#0'
    'VO8Aj{hi-MH-A-u;eFc%Uj3(W?+BHX=HA!yKlb=@SZku69ra1j_(S<w%f?tsY!t(Xc~D{=bLbDK+93Snsf}ogm`)a}_~9sQcy3H(E`eLanZk46'
    '?VVNGa~h3Tm;K9TpU5R^HLu3Eva74r)^|FOJCgDw)b};TW-^kU9}D5<`G@>IHO(5dZ#p_c#2Pl6xxdgT+8R^Ss7kJz)(JfQZh3$goOqb^*Y#Qf'
    'eX3QlB<HQHKj4H~jb7GfYV>NNbd`HfM-`=|DUYoa3;gPuRs*uT2=(Lrb-Ez!#kwl#3Y7(qu0L(Sd82tcoz41l?69nKZkx@V2bUKQuMTVL-oqgu'
    'OauQu%V7PkxIInTkH)|8;&}Tc$RldljmAVRFA$b7camTR1GBxhr>9PQBsM&2u!m&vScbeB9opmWp+U5KV(DGmfwpW-1|5x#X*!8!7kOon*S9%x'
    'RXvV5PQ<#~8~L16QUorukAxdqZOH445McF&@7!W`bwWrjSYO(cktf~T&8wp^PpUdZTDLA=r_4B}$BRf55H-@vabs)A^K<3aZ6WmHBV4Xs`N32r'
    '`mnYq2xSY~%-luyzoEv{V7|x&a{tpP^{Pio?a1sxYSnDD;nt4I?%T{bo1birUo1*(hrOxW?Jv)VpD#Kk`rQJB>-}bx8qxw9a0f7=!9m$|Rab;p'
    '#cWkJwy|9^g9BzS;1Gdk{m;BJ>5(d|_LTXH^Z&uR*;T2oHIXin)5!SV<*necM`$j;f9)@e#rh3vjLQdEFxggOrR+BuuEOIgP!vS~9jKwk4w`x8'
    '1y|ey(PJ5@f8Oj4_*|>N#0R)-Cg$h(GBYrGwg9hP`QihqwM(3)?$t-~NywQWmrTJBk;NOdm?mTQ65ID`r=E8i(5(w%J7myKO8ZC~V!C4nUe%X#'
    '-zrusm)`slMii7<@wWOy6z)aM#5K#-Y!VAij8`VIH=;)lWw);}_c)wOvFqIg5q+*IdtF`CfL7aUjbPysW&qvfCO7=^xuYMw0QCi1`S9-H@tIMx'
    '&vw=Vw5EX;wHTm4#OaapogQ==<nYU=VY=l<Ll5?4bp5EY*CeSPMTj4UEDH?}<z~Y?me*`CSk<T5Qt8a%^+Rn}X-ZV!*tk^0-a#@lH;J~DS*Oq1'
    '^VM`a<WX!9BoxRiU&%DOZtu4L=ytTH?!agI^_XQi5ssO>?d&nj?d^R{hlmD=qrFPsfN<%^DdF?sOz6@MYHZ^>?cZxB$PlW#o3CA^38Js}dt@;3'
    '%=F^jbBF3p<t=&I^`_60SD$|hR%s~js^7zfMB1F1TxC@X$2oj;P{NPg;byI#VVXsoKl@(9Un=N0=mNV)QF<pKQR$xw^iYkIDi}jjXK~6i4`9NH'
    'alF_<5?<iux%tD`OUgEyS7AKV+>&cZ51Yc$fHb;!dD}l{4|UV(&g*<iEKK55R@=9xtHN&ZFu$_>SGB*xXq^oal4Zg$seH33Qr4e)5~>byI~+>C'
    '$BHKsDef#J^Np@P{VDkyVb4s~P2tqcJYl&i!(;bQ7@{z#idKIjEeL#b(vC+|ahGN>Z1pE&w7-oNy|=s3&8Q>wsds6?p9k&Sf%lQVDA{1tXj;$J'
    'dpP?O$z)Nl{q?|7-d3oJa@05L`lr%AC9#3KZJWO=qI+E*n)VUZDovn4j{t~oc2qM=2ep3a%|>fGZR(oe@AZyZzPS=FV9cdfu#MB;+@3Ssc;NRL'
    'wNtr-y9sF1rs_zQGi3CocrJ4<>mT?0-aGfI)tY4!^tbt(*z^x`h=gS5(c2vgKf{lFCAP${dpS_tGiz$`;;nz%>Y$SLZ;jG3uDzt$aB+Wbuw9zS'
    '(hDFdGi{yY*UieG(nA|GE)S=Hk*<SscfY2bLAc85B;6i({fqP4x(2u}Ukksw`xxTg(dR8cu&Bim1f}V=x}VM+cR1XD=ism!cpG21R~6x+X|Hua'
    'BDgROx`AVG7grkHJH)(-gMIA4jEkk%sx?m=f_JO>(qv24zN_wPbGi(T?)yPKkP6ps#MtBhr-D7YZg?B6!;`~J%sk=)V4=HWbi7T#Wb)QL*c{>6'
    '@%nxwpS)Ian{{Y^zP+f5?8_u_0VOYBL~V6~cKtXWT!7QEdhq`A<E9ov^&&N@rm$<Gqs_$o^|AZH_&s{Vy$MeB;Mn!iH+WgzyugvBEmnXQ(Q^D)'
    'x(ZsK9L>|>-1Jf;@-chWQ9<hc5$~I)bZ$@<{S!ZNsOLn(y0=eUdOS0CQ^dP^+8_o=O3AmAuMN(a9G~>21=QMg@(yoX^L=FBuNV5RrpOsiJH&1s'
    '4$iyVVf!|VgU)SQ!H|6ByR9w{B~(M*dF#c!V`w?rr5N-L)-^ZpwNH+p634`~-@9a5`e_<V?sb8!gu&^D_o64%Xaa`8A8($ekEeZkJw4bX`5}F9'
    'VLLNmV2EvcH*w8(%62=L(TjR(D;UcqG}$uq@?5b@p2UabKH-dS)&Dx~GHdx55vsHPw;Lb%U!v*t*`^rZ{a5j{_>fUL=RhLLvp+nM@5;*4Rz<%M'
    '`I7(=zKGt>ZoGx@Aip<{<My9NB}$OJJN&$Bp3FmtDA&B^e~1e`TRoJ1#9v0*+MY@EHG>K4S=x;r+$RM1iYjn^>bYclW4`sZlKtBJec5rux@8>-'
    'Rcmx6znPrSdCdDmxie8^c!<9GcdYvv6J_t%Zew&^FgI=Cj7j!|CCF9#`gVGC@`UZHHHTfkyN`S|ePhKa&D+Vm7`H+=SlSylpI4xicuo&hh>BBL'
    'o+a<!X?gFTCV0kz{R7*>w@Wy4yJt&m*U$ReQdC)3jdRBv2`Qm=)NY~K>|Gjs8?i}lr23MxN->n0SQYv<UXt6NC19J>u)!Wh=x6}#0ch5qor=-h'
    'x03VZW0?_2juwATb2%@7;$*Bk%g23p(7(!vCJU^(l7wg>zC}Fiv4zwA%o%Gr`giJfEsh#N-uVNY5uPl`ghmhM0rSe8usYvH&g@03bGp&$zuNBv'
    '!RM%aW4*?qYEF!4`I>fJA<VvOMfUY*wCR1Y%wjqkio2_T$@XLSI24M;X*1C7jWeQ*ySwc=XgxbEQGIo$`7&4!utn}94}Qo(f<5g0Wrfl)qtO^+'
    'dx*4fPtB%Ct=$}muxI0FcL2M=vM+VJvB0POMCSIWeyfJcxEMKhuQi;UCJBc`v%LYU@~u4uqx$^8am?;oD3YU(?%uDZ9Zp-^J!r=j5;hJf5$ApF'
    '+&R+E;3jU9cX!F63v@RD5E7_GQ{G?RQK^6U7~Gpb71*&?-y}z-?Kh?2o(YF$dqQ3D<zbs1!<12RVN6!<88ylNV#^WV+e5S(bVj28c$Hr}q;N48'
    '4CK|+$CI7xPkxg<yRoa~I~aA0c9ZBYF3k@{rS(429RsuNP&iE7gYlZ37SBTEJ5kkw#8)@F!`Iz<s5e_;WzgqNpp)qsS*uor2BqRYi*+>KzX`~-'
    'y!NLuhPp{Q<$$i;>D`@My*n?%<khNt0<In;m4;CpY1!vwR(TIkn(*-TL@HZS6+m(nt#(rWd5lCroMGAZ;HlhntZ#>}Q%=#}s2lGG$MfF1zDMrT'
    'y-+|^<mp?>*me{tte3OfI2;ToUy^oXO%Gz|L5rPx{cv9ivO0@e-vMbYzFv8#W$@&*>dJe&Iz5&(c{90_o1rd@0)Bk0d2^wWWQL(P_bYHR1`f6*'
    'msxAQ+8x)!?SL6pWK>qrlPgU5>9sE9<8tyI@rMihSp6jluuAuDLO<#p<G@!P?v&zQpX&My8G2qNyf3WjPNDyV6kIfA>kZ6>Fg1vivwLD2x9i)O'
    'kCfp|DL1`+TPJtD6fh=9*Qim!p*{twyw4B{-_L*H>gm2(!_C24_ylWzQ0TbgXX6?`Vr>&`p2hA+pNcBJrRv(TTi5)1B_tR7PTV~=g^*lvwrzcz'
    'ds-F9#-!QT<EPq;Z?D$o=Na<<-p~C1+uZ2<{5)Rbf9D?lZ);m5wHue9Y<5<c(X>s2;ps2}*ki3PBeh=r`>mML$2@c(Cxvt6x>_F3Z;bsTib&3<'
    'X9D-sS&}6(!RM{8ibcoO_^MV<_w?^C%{%R6Ce$xWE)2Gd`(;^?=EZY*I*QT|B(g`4u14p_+rkYKt)5zheOKUQv&pf^RgnAR_&ytYJqITA<@iR+'
    'O?Uey{wO#D3|%_EH|s^V<94(6D+Cp`k&77hVyZjoH+xG<k1!*O5@2qc#PNA_-!{pRsoT}wGJBa1YuA3l;F{&|lWy*&FO!+axVZHDD@0G##?_fG'
    'yVbI8t?2jrjOhz7stLMm4(RO^9MUt}Klpve9Q;ub&B{yRErsCteC)L(_6&9yQ>q{BYxmP-4<|OwwadZjFGrVVp)Qxh<LN_c^xS#=*;xlP^%fEj'
    '6ntJc=;KCtyo2HrzE!7coh~L<-zy7oH8m#dAl-{;)NOP)xo&lXGu6Lq!^hUkDdDL`7bVJ%za2Yy#gG0>Kl`4Zz|{CgwpZ8TR?fX16MEWA99CO5'
    'Z%EaG^*5Bh@QRODDb=dMCvkb{ABu;tuq|{B<UhH7ICL|np+US9j1Wh%+dp;5_#Lk+n_em1m4#uv=I0by=*SwF4T-T6XpQ#Pp5a{gmh1qiBZXoa'
    'T~=kqL+VYT1>Q17-TUuqKBqis(!ZXUGOZ03uWea^wHEM28eXMifTtnmOrJQ%-z{(atsl0V&&(c32*p42bTrm@wtJD_Jse8NX8YFw-Rw9E^v{O7'
    '4gLT|+k{(<pNY^%uv|bwwC9aKCJ^HEsoxyFSkl{FC_VKk8mHS$e632#*biR%c|H^fy=x{utlSOFoU_IZ0UA=@oLAP+>UK#x2YyLxN+boW#>jGd'
    'VTRT#Cx>j+1-|(wljBgDr087yOSt90Csxa$lc_{)V3L5k)sTFjS^Y0;`bP;u39J#AM|qRL=jIX?6J&eYB+jyDuWC6h^gQkK0HII6+kf%>fCEg+'
    'lZpz9slecly7=|r>?+Q)xv#v$U7+;Z%a>VN;6rxIxqY?~TRqPGd^a56N##s7h@YQI_f>x+hplqNtmiOoag;c|Q5%0Rd*E|=U#QsUd9HcW>%&y?'
    'S&@aADg>k3!Ozaltfg8etq%Kp!uZi+e1CbFYQmF)UHpMhmGX42L~dO0H6}c9zJGiQ*9U@Qi%&f?3aLLY-;d$@3AZ<!iP9Ln;fm*D0}0m-HL~92'
    'C(+lAwORv|H}j05mw`v@t=;|oq!!-$TG$~SmA>|MCAGH^DZH5|kA4wv;#s_h#^Hvot&77YiU_U=Z~PBsANK(}-S7?0pAPpF*js*2)UtN@{aSt9'
    'FP?2GMZ8*$3-v=KSScD%&LyJ0ACH~pJDGq3&Zs8HdfvX)6<_V5FwM#5-)?;@h~<*6uk+FFa^l1&zCPWpuSP5VFy(}#a-B>MvU51qTaT$+D=*lq'
    'e~DalI3^m`==Xj=Fxb3(E1mseGfCH;qnQNJ7)HtITH@ufimE|)47{-iUA|*qn|_PhnG>bc3~Y^BUAY%sdgh<&IJ$Akja?mPl4Q8!`N4S(RwjtA'
    'KWoVW(`_gU=8#`ocEfNYRk=w?a?NLL89%BIajle??x4;4?nPF_N;;wk%}g~e)%vOpI|K3lKsycaVmzHO<&_LQa2309#m`x{bYlV0mW!7RPlyS^'
    'u)>4u<h4=z1n_HljAr5mhE{|6?H0bKMPGkNfC*2z-C%FT%j*}n9^?%=&DN{wT8=hcrdX6$U(PLG0}LU_x_7R=JEN1!<#IMc31^US#w>)PqT2_b'
    'R){&=THlA2cv}w(j2d|={ta4xPt~^<FC4|TEgD%jzc3BVWERM=c`2viz;3@PovIbn*G{kyo6cgKhx65;MN!gtdw*<aY4?{0_f1jTAq}nSu-^{7'
    'c>vG>Ty7vgeoj>O^S&T$VubW@&jDca&9z44Hvz)x=RM}AjWX_ht@WrsFhSF=g$+QLq|=ky)+sDp4eocbJM9~(;Wc66I7uGF{={d0tlN`%sa`(W'
    '_Y7&V)_d^RY{V@t9qcMirx<!)>-6zGZPe=icQ!oLw@P);uJt;?XZpL~Skpg>;;T(!TX>3I-q_m3+T<wXhPmfE-|b?4&AWJgXr)zdK`o0S?T5S6'
    '7I5?N*D@w?t9gvH67QzpT^uHM-K1W{z{?r*@!JPk+LCLihTj<E?RKV!`EuwFYE-ZJTKW%uV4rs6{r3&>_$Ym)bN`B|SBl7;rB|6Ohznl}uaCF='
    '+b;0Tm(wwg)=}VeWo|&Te-o6-c%iwY5?cr@P0t$Zb8x?r1oJXL@88AfTVk-B0OOJDz4NL&qr#Cnrsk#-*2E2(<jy|b3fIbMR?&HbeW%4@x&x90'
    '#NR*Md;rtv>^m1cX2|3X!eaE}S(Ewgr>1Pqxc6AYaX671=#(9=)=lU2GJfW|uh`6=vdCpRGZMc3ZpthAw1}65xdFc0Vz185imhEIiMU95X6usd'
    'N1{oZ_xtQ!e{{$=j){x@^ei)|O@ZcWDX;;kc-yM-G9oU-m-X~{oDsj-I=sVoy07=!b|=BCr!W4h;?X67(V$wpP$?q?)d?~lGSir{ps%)BHk{qd'
    'gS_aR*QTR`dXw+u@_C+3nwPBB&0PW6wx~fQYa?Y$f*Z14vQOo>awv0ife_YP)YPI*-Gt_JkDrGC8D)#nb%sMVsS4iPwU0bD&vjbZ*!HE8Vl-7-'
    '*QX-OSzJ6)=EUQ1DK}}>wz?F}O-@}>yqdDv1mSsdybP681-~XQHQs-?qsNPJ%pY6x>83pOl6(#O@!|%t#ifzpD}B||Lz8)!u$G)JpB6lC#d%mg'
    'uD~VZHa=_U1ru`bl#uo2d#ftp7z)m3y=3YdbZ8E^tb~4L{RPp>UFA7QdmHC(g<b+#-gut0B0AO1b9Ty)bH(T{XeMI47cJz-Q*I@;2Sl^N-RS{&'
    'sfY{Rv##GqbHz&oA4VFB^X@DykN!NO9(<>L?2wZ%C0eC{;R04wAq{L}<J!CWYPY@ULTZ77jygmJ6zHloGSv+uPBRw=UBCEoXew{O!~z&^;5Wj^'
    'uY=Y|>VeUt?`Fgn!EeQjqTgtzyG{G`tHBW$dA@u`*TMuDxHglg`m(c_UWayVx!Oloqh6lqpPmxzBW)>=pj3a3eqx~h_`_ab$Cuswp}4g%#6G~?'
    '|A0d__>0{xtuasgae+*sd*Uh<<|;^3V6`bV1W!k-<9SsSFu#(U@)NJ1=mWXa@003qL7VF}1EkRLg_v)AMQzX&W~M3n(r&mpQ<}FemF1K1)776n'
    '16c7&<PXlTK~hsU@!?NUndXd$`br<fo6uhYc%ZX6Yqc9fGV7n3`lt*FiDDquA3^Uf6{7}SUfF1l`BzTnYlm{2l-I><imrc`tmO<hxIH5M*`AK9'
    'OZs9^brSQ`o#uNIR=#$#TtT;b3N2z+z$0OO*YRXh3GB~_?AGU_{k8s6>;{zeQm6pQRS?+mOIqK)?8XV~a8Ew7sJFf6Gx+p{x^6I`yqbJ#*5kIK'
    'a2|PjtJZYdTS@w?)AT#-nC#_ke49P{gA}<Jq`7wolHTDI%QyM9GMwU8#r(ZPrOH*)J@gB$`cGOu(hK=&+SR&nkJgJn<dd1Eo*(OpF%jEp#Xj5@'
    'owt1D++%$ff9km_eJ0%zHrh@^%>$WKjzqhyAv{lArmN4gwO?Ojr=CA&7kMzBlVNm*^%00o*DZ72F&5k|Z+zi*vT>$D`2Gsv#*67}h3~ty;Y2^A'
    'j)%C%k<^?gA7OQh|D<8pjw|)6x^Jn%vvJfoYOyNrpEk{%{n^_4IN%~2qz(D64MV;f+D@xGFjZ{#IEX@c*l*;TcU#q)n&Np)O&SbU@k6$1%O;6z'
    '5*{ataRW&e1H@*pb#*mZghQL8x=)NtI~cYeY&?xLU!M^=1N`bB)hGQPypZRIaSH4WZ4cage>PQnu*$$UQ3wIMo#+P*CeYVDY|H6rE&b)_WxTI$'
    '-RZ5z2K&C&P5uUJ10w!?I{BX+on1W|nMQJPGe?(Bu_K34Y=Ioxg?2+NXP1+R?e3pjK&x4;d4~Nov25~peBFLkAN_5~H*VY{UY|Z^?tYJk&-B!s'
    'pp)Nco5|Jdu{*A{YG^&D8^c=9TI9~L91l1pAMvd*`B?25+d)%*I><}Oe<Ovr?>P^9osNLS#O=|&&4d`Z)|pEFC}z(=E8eO}C#G8(dM5Fl3M_Zq'
    'FT1(dKmQJyE%myxcm53q{#`Cka|lZY89zz}e%g8UjKkhO((75J1FGYGyos(-9gVEFVy_m5c~6ID{np!Cycz<SgZ*K<%~hgz7s7q+0ZP8lyNrD9'
    'f{i=T2rv))I3&UQk47^u$O$5S7r)18J3XWT0WY4j)}mOdQ~#>$yfEk?Pa!w*Wk4h2wXKx1C_bEGMl#&}eD}<&r*aT)zcJxsJ#>;+w}-OyS|UDO'
    'V-vBnyqsCKG1W6g#%j&BPm;A~yXUW~)m7iR!*up}4~bJWvi&n~T7EUn2aj-Ac(>Njd)0c24)j&z<9QGVLP<0dU^A>u-_d1^JCUUWu9vfDw&Z+d'
    '!FIwyV64(5u@K)af$h$!^-)ipaEu8r9^s=A@F~-KFX)%K4S@RqdMa(gGM8-CS!#*#-AGz<g*11At%2>^$DM1kBlsv$@31`&n>)N}v>od9-nh-W'
    '^U{Jav~%u2^vT5Q8>^ua826*RR@-d{rw7;Vw6Cwax68>;XNP**1WvbN!4=!X)cNgZ?O`{q71e0`88y*^IsEjUwTE;NDo-4gmh2z3^_qvxV%Nhz'
    '`vrPV^CqG+!0w)Xsr^3q3Tsj3va7>xn^x9}$791SnSP%jecEgO--{%#<Vg%h7pR=a{tf$^|Ms%tEClIIdo5;AVH}3Y{?x(0T?fg2a<~iH6xm&)'
    '@5UR=JAWG5V;|Ub6VPL18;N9<iP}h$XczfvuKv{SZT#3JKEic2h;)N{V)+($4b8RNp|#)z1`l}LA($I8pO23jj$}P9p5<>DALd6ojbXy|-yFgH'
    '%|Uim2+*v*ZD7MY`*EEu>G5B{HGcZ976Rs!g)6u98Ik$k;@X0teu3FmgL$rxn9}B<J@Q$<?elrTPoT*Hs-*!plsBj9_|=1-uB>!;ebDFU%i75n'
    'A0Aq3BcVM1td{N&L*Ij6sOKi|K=$1rIdv)XvGuO@cw5S~$r5oymrs6If4(XKxLev~xDacrliay31~i(}t<GZBrrm9`V=%%4=<(>Mwqp)((l-wu'
    'Ub<(ZfR5jCH8}y-ySt?03R{!Gb1l?p?$lD(jrw!KGI`Kip7L7-rL8Y92;ykNf=y-l0M|4eKQ?mnaD4!9bq=4yoAhnfc1m@Z=KN#R!@$oRi(B*r'
    '69KP{ZLs>v3+N<uYE+!0;Ja33_xcJtF(Z#1ybj4ZodD5bLXkK7@g(1LXCs@Z<IuS>)LfT-Et41$nVnDfqt1?6h1Xj44VTX$hrG`m>a^;2D_qjY'
    'h%gYm#@_6pH2eK%hp#@L2|lHG;Xof|Csv3W#3H$Z{56A|*+cqVrpTN|SaGh60`@8087dRQsU*MV@ks;*y0&OcH0BvKnwP#iDaNAED+=d#*#C{s'
    'Lrj^Mj@1`5O&cauu3q==d6fCUQ&yiMwPgXvxO#Bo6xZgiSf3)vWR#!aw!uy3dI~J{-fS7D*Yj}Z>RTKAUIsT@Jzp*s44b-NbcPJ&oU78HYn#xq'
    'G~$GoUncVN=0)z~)06elU-*2yH2~-BRUb?@;O^0^b=cQG{llmF=ncImy_AF1P3#5SRKlN898|ZRS<FSa1qKhXrRqm-C`@1|`mBK{3_8h;$MoYe'
    '`)&z|+q8aJcI5UmV?f>JMq9SWYvZ)sKW%cv#367PpN-iWh%3|B?yzrdlbJkvd;XT4vMtm#S31axLVu^rao4)NHnYZ!uTa_WLm%eO^McY`i+c9d'
    'FSPD#vq!7e21tDi|JqOdEL@>cZ6>0f%RRqGm3zBWNXh;|Eb--#T-~&SJMb3=XRVnPlWL3+nz)sp*Ndj^xzqF-bcbuHy!O&`RdtZX_&(P~*9WR3'
    'V+*M{EGB<oyL3tG+nt{gecgsDMH7-bY5eO|zx3tws4G~n)7!vaLyl6WnW7;ezyEmh#(xy<QW|Y9sWW)gIzk({{1x6tr&v7sn93oyT><XMo$?H&'
    '`wN?*Jul~rIl%0~hIV#aYJ0A8m!tK-o2ugV_V1Su9;Sx0W5<w|l9y);1opG{u+{>S;NhJ*j<nDGv0H%tczwLS)YJ`t937NE+!)E-<L<Vr0Xy-q'
    'OKxSQYmqcW+c;cg8ugiH%S-Oxwk1AW-D=LB6P+)>gxBMI`n1Nv1VA&Nsrkf8Zgg2ZtXXEGYx?k;q>Bz_)>B%RJGol}ejxcNw$Rh=Wn*)NR_bkJ'
    'MXRlh)707@C;5;(Y#%R+!!sEF*uW-=Pv0ExnQ5|`2<Ki6BoB03^-6lhYK`f>;)cs_-`P$Tm|U;NCdRI<-f|R>)qZ~MG#z|)5VLM$=rr<K%>km;'
    'HGxZ9_78>wcHrKOk(0I6Z}#66C9vv;hEd(ba<a?bzZwp&mERI?GOzu0KXlq;FAg9_NTkMeQBm;(JZ4I=Pg#JeU?q?N2yB%TVg*^y)+1&i->0WB'
    '=<s^BQ?{P{xQj>j@^4qs{9B=iAv)wd`o^Dv>!=6mV~l)#oJL#ibfNCgWYVtf)}k)Q2m=#c!M2PL&E(c8u4{NiOCOhZM-g9~j<cGeGoiEmB-G?e'
    '!SU2>Ye%|)gR>BKdY|QV&K~$DQqHcA&Fb1fRwxoxrNEwwm4T1%d;A|y&V>dxI^1SO2<x|2^Cs;d_Yu__%_llgOD?!~<Y5tzyxnGiPyQ&QgL2kQ'
    'zG~Qo(FAfnytkIsIrDzS46p;QKnZHleOQ1Jo3`!*o_|?+zVLtfqm{5yx(iR<->>`Ybk^AZL7*aEy&CC%UMZ&<N|0ap)n*wC&Ss~*sUEN)h;)B='
    'P(v%#XGtErhKsuw^mg<*LE@y(4rnr;VSG~o3Kdztx`^5q-jQ;&x6<a5TR;w8oTiyYqoW<ZwaS#79>^=u8~5rLPEcIM=k4_KJ9@`Zy+1oNU8|!e'
    'y*YKq!GPE<Po*@YwoLbOnST#M=KWV8@0GWzfG?5%3B;J(U$U9H|ILUh0q-m9<XV3Oy{T}AjJok#7vHJ>#}<62A|8RqQuI0D;H~QZk*HC<P=sm&'
    'ZH^pAE3;eF7ZNy`;5fHem;SQw9;e<$-=M*!ebx$Rgbu7z)Db3OgWt*XpH6(^6;l~#?JR?j-FIVvyH#`dM`q=|E8Kh0t+P{UWv<OyV^1}}zgpdv'
    '^?Vz)2|iQHO>*6c<8MkVjM;JF@`$|EfzgN}3X(fyxU^l1V+z&L$784}(GZgd2567m+nKwGm^x$MdviYeZSFVu=oRz{AFb;gq7enGtnS8pNxYqr'
    '{M89413Jgz-GktlqZw`Gg$!q6or_<2*4iOB6t4Tn^RMksp(~PJ0CMn@m`)k--GT>BC4A5o$L$G?%XHV+54*$GY;zYjEA6owROzY8Hkr!rye?+@'
    'VrXTp_K0C)C`4{cs~-9FyPa?x+d>EG=&Hh%=?3JzN2YKtlK3$Nu8-9AGw>_>LcNM1Hr`zu&^rw`#Jg2Nt6}Q6gEDws2fJx<d`PZaI-l`=NQAA$'
    'cFkP1;?{{4qrI1W9?0Xjv2v&<Lp;a!EwiFQRbR|0ti?y}?gA{~{c68&v$IQA?1>GT7bMV7<%P&}cg~IuX}@i}K_HVZa7T?AWvpb=cidTnTc%1@'
    'GOB|upfH$Mp?9$!&D+Iq>WFU~jJ*CaMbKTZFRC4AJsQ#iyNi)_<-2@UL|A*i)2LqSK9R-N!`X`|*)8td85YZyW(|Aws1(-)8<r!w-J6*ct65OO'
    '?fZwF-WEH%-s0QeLNp4)T+PRy7G1P+@UJ%ZYYY6e9rXiAS8@hcajmdUrq~9bjqg$`WEgL|4eNO^VQEG7D0Fkl&4E#gc7iJ;uQSmlQ)_JZ-%lby'
    'Yrfn4PM1anYg8YT^4qD;XAMOZ2GQg~I_NDRm}Blz^26v^FM+y7@iSK?)~r~w+tfK$!K|fdOP~Q>?JG{+E%{87CkZ9)@AFdI@<N)=ghU*JN0AB*'
    'EF1RpZS6Uzw-RzyikZ|4(x&S3Lm?MHX>h`p$ZId2Mkicp1Rw{biFJOE$7Q$FjHPK=v*UPvW0xi?KzLC{RQ?Sg?D>9P@SEfCNv}T89lRcf71wxI'
    'Hc}c)?(kjek3QY#NB7~4y>{1+3t7*A$F97qqwxBZMsKL4pF557kY2RT{T(g<6_<hrdaM-So){EfORmj<{uwR^2+HC?^`Ui#joVCDIgn#UhuQGH'
    'xPG^82`rWE1MiG!EJfryMdAD7m|-Bl`fE+C`QoL2+3G7(&l01X9(3r@NZoo2E^M`4|5Kbf|16)+`*^l*G+R}<*)qSb!d}@q*Sp@oGf!AAM*8^o'
    'u8sU=y%U+|;yho^GnM60d}nH(xVwA3wgW@>3WF<Cscxk`YgKR=udau$-?+oja=qcNTbH%9`t8s5SXh+21N@9zmcj+!kCD@{o-=6VZ6>R+_1NHy'
    '*NA&Vb!W0+L~h&{3RZ}DkFYjNqg57*;ns!V+j4<1evO?x=SaQ&MuXq54jJW;U;Y)(VAw)zx$RG^ARG>P`f;rSiVh6<Q?-`<yW5(L&F5f_1N1$s'
    'kXri?j9*~I{7zCNHc{W9Ued_`Dp-Eq6eqYjDY^<ocf0rgB*;AqaTHu@I<M!!`(O$5mi=t|EPqM5YF?l4%fbn#%I(rbAF8TzbVulFB+{ehtu)&+'
    '^mltC;-qV}g0wyoPLS>>lb~)1Gqyvheg#EtP}`3#41oa^%B@**7Tx760P52CsIz@3+(wSz%+s~F@6XRz-DC#0zxFSw3CcDRb0)oE4oB-5zdu6~'
    'HgauzMQZ2cx>GCZ6LfDE$$O(4B0}pa)lJ!`-F3>f(Qe4NNoD(PJMFG)syYGGz-li39GKfS2I$$JG(S-H1ufPjGV$aAlI?NK1(w`v-ESU(lD~Cd'
    '4f;8#j`R)NUb-L9vYftf)_23r=Mx^^$>czGpXxU9ZF<xDhDFWcROX2<C;O^$BacFYbz~}o(E1!Wu7>+bJ~6X8cbsl(Gu|C@)?rbdhMy>WuXmZY'
    'qP&S9*A_p#y?cz>07eSMseR$)W(Qt9-fPfkN$qZR8O1m<D_hy=kJ4|i>MYQ2@7c!iE548Z5+`F%<Nm4+Offs#s~3tL1M=<(3cX#8H{9^~nb^)B'
    'yAM*L!x_eIFbn?Fog|>+cQ5Zsz3Z?meti!>QS(&6k)FrpaZ-AfnpjQ9YIk}fHJ60~R(@dEiE~?_erR!1S-;F)2{yUCX1fu;UwW%W6`(-0JvVK('
    'sjl9uRlaGx%2zUhz_1a|nEUg+T}-%#!&Ig^@$#ssqZXsj0ldBX!wVVyz2we&SG}_AX~A=Kb1a(%3IRxt6>Fd|cbn%$lh@rPzP4;pZBQC?Sf+0r'
    '^5~eLC9HA0bviws_J_2)`im;6p&lAGv|FE(KAWB0-@%Y2dh{3!MFNfv=_-P2=kc;p*<VYvG^6vv3&=aeC(jRuL_!<ldL8ajFnw-YBFlT?it%cy'
    ';*ly&{L87FBcBd3u5Y^FWb5Ll`X)j2h&Qp}7Pw8L@{wubyEEnZAh5l~gztNg@-_)0NE#^iZRH;276=0%ec5=hydZtWN(bWfS?nv1E`{W|)`*bo'
    '4dK@{?q=<^dnRQIILEa2ri}gb$P7>4_V$Ta7}2{$7{<;<#q@7#FPLp?dgUkNt8ClAz5asZ&TUz-tZvNw_KVfIQkiT`Vh|qe{u#}h%hjtb7-~W='
    'ba#TauH}$TkM&m{=Xzdu8F@DcA~~*BmjvY<-L&iAWQ{*t&aQ1?URWhxYk^2^y|D{ia(^;S>#o~91lM=H*kZ2AIRa8zWL=P5$oq%^gHSrSbw`UF'
    'ea9$ZHz&fLVz7O5y<WEDs*Rz{-@<sCdZbpja>{T7LwlTFYb^Yopz~l<b{f%g`@BADlcP+T7sN`VZF*XLnkRc#`IS+Qvlub!J9eKJfeb@b@q9FP'
    'V(*WS?+c*Tnz7!smz)fQWf>Mj)>CnQ7<a2l)o>YhE>g@yd=r=?4=?Q<$^7O{|31DD<p_v+<|LTqkH0wBM5LP{&Sb1+DLIO5lmhpPcOEA-Hde9G'
    'Cq+j)=DJj(^VueVy&8>n0W)8pb~&C8JAFk*tFzG~o(jicWLDZaQj4^;0I8w3B($7_mVca;(|O7uLv&puoRT05R&2q3-`eN)6Dl0x_Q1}Eh1X;3'
    'e)Jl1bAqOK*p_N@AzT+0)g!SJ#%*h5W6#>WJuAk2nrs8J-JDho@&a1!!o<Z$3EF$vKVB*k`)H_rk=Q@ER>hSL+YEZOk59|F&jEVLY@o&v)Fz`d'
    '3-Lpu_2SdQ3%(u>e(+6yh0ng5y9xjJ8-%3n3*Aq)0+%2|7!LO7jZxIIZ3qFmIVzWl8Fh}kKa;kgX#CeAAi63~YLx6&qO#fov%}<Yt@D-ia)C22'
    'n<2sitGUwWvf)1GswADXl?-xgRczJgsZVi!-hAkjnpz7OLz3L6kgw=#%yds$UmH|Z^#s&pUFg;Y>^ZNDPw=#UnwfBWYTjx`E2aMGrn?_jok6sO'
    'xBGpNv}%7|kOA8@6yJyJ_8a#t>2wT&T9aHCmoR<Y*~=)379#9l#r~>y3bHG+o@l?(u5->$Ax8kClgc2A@8Yd2GVbsxaH@u=DfCMkYF=}g_Gtwg'
    'ZpUl)Ww9O3gWJDb(q_(_XY*G(o@J%~m|4V9DvJ54IBu9}<B8ttEs4XPc&-iphplsMS`Xaf@Mkfqk*1l5(nxd=m7GF{7Zpi_B!{BIXW!3%zuPnW'
    'Z8ME@uk~BkHSW398dl{cyUlysY)sBDMO3(*0ILTqTHWj65ET?y<Mi$5M^)3xzf)AQE#6r+4<Ta=wW?c}+Vj{lhQ0{jH})j`-<^kYk-E`M@RIcZ'
    'Z6CP*L0}Q1e6V;v*G~D?sA$lv{tiGl5f#ZXYukt3qLs3=HoNJwCkY3@yNuv29&Y?SIIeCA(^~JA3_8mAe4hAt1!0wEZ3@{A)Vn%bjV<!s$4%36'
    'eKO<bmp#qT%xCx;<8HnF>ep=D8KeNu@Vdo*?ahBT4G25xvA9VL{!-LRldC&TYqSOekWGl)vOQ4cwsYjBL;bl?l<jA<al3jhznEh5Yp<)>bq>zX'
    'l`puLaU(+RGy5lAdxKcD@4?}Ao)DGbI-L(EufGoB_%ZouYiT|?SDr!g8Y0y0QB!736=%LDZVApDTtvOBS809go{h6a-H4J7I2kTd=SPUWQ_Xs5'
    ';fE#T-US~2wiYY)aJp01*G;S|D~sBo#<tOgc0CO_@N%^^<1dmfnE83_x;Jy}ac#1341pf&?_4mhWf}OMO3OhxDeD8{07`Fe{hrS^t-Jz@Q@<K#'
    '#+g-=8FG0ki-oUjQ)?BBqlYw?fhoe69WhbA{-2%ZID4;B7`2`}Sqs(_z23>!Az0l$!oeyHSn1@SPif~c%b!Awjw(+q*GLxYtM-9Mso|!r``CVe'
    'bst{kmO|=_ul14P_57Kqe)NY-U~kqL%;`D@oP+lmDQ&w}0dJlA=-WA;fg0b(%;!i1@u8jF<E2Y6>DP!pLz^9o%mwD6GhVDLqXl09xgD;8&N<kD'
    'y`g1V>B!?3e$w(}p-)$4pnRtiF8Hom)c5k@pWT>A{rins5nUmp+uiFuw(i;kN=AHjs?obO<fTRCa7;Zn*1ugB=w1(^{H~Kqn&h$LKYma%neHF<'
    'aV&gl4SF9C<Kk1xD8o|@o~@Bj>GybaxAyFHKz3t^K}H7=?i}$y_`AXUy)FS3aT(&f&2=XOVM~8aw(B1;X8CoHL6cRF>**M<^8B-`bAK}h?BU<}'
    'Z#&*GG;kmew=}8`*SjHJd+!PTcEn&HaYOZlxbigU`d<}Ri+$K2TYGku5J+`fbZ^bW7B;jU0S^`NIE;uG`rU6*>qFunV2vjqZlv;e5)?QIquMvo'
    'syNzY5R8Ydzsy0(&+Ar-J9B~LpB)ebl2$>=?o@9{Ah-#aS+!urYVw)H#oOKdP&*IwGISgt^%q2dX#)f(h1k*e%BiXX^i3PynRvv~UgI)RA!Z`h'
    '>y5~~c%3)CRr*6{VE+NJ!{MOD$>^mIxwqo{X?XK(c$X?uTFy6CyikiL0qlnB#)-0m>ia|70H&Lnj(k3=73;65LdiLAprW;jk=cXp=US~AF{D{;'
    '6>5#h_L_yW-mE$TvhW%xze^XDm*(oO5yzvXCdFw^Z~M=E66jmXdAIR0`pMad1}rcnE)PHw)#_Y_Xn_vtQ*s*kt$$}yjj$s6Y6BF})g8$!8edId'
    'D^Y&hznrnbHoqUSpFh4&?&i+bCZWXy9xBAu+l#*X>}=`QYEWcsy>M;(OY4bC-tORRz<SQGceV&_oPAp80_)!X+VneR<2MXSYcE5M;_ENka?dod'
    'Wfy19m#J3VI$8G|QIV9N<gB~ij;2qrCLt9zynQA!hs(c*ERW3DeDrLR?ZHMJR=*Lx+Ay_*pWI!b?Bv_-VHooLYP;H;)wA6uB5$L8;hVRP#PgMU'
    '@P;@zhNxIache~&-<!~2)AuUH(#U@M`Ga^<_j^(-gJqH}CV2lWD}4l6VgAayk>5(GWum5%l?60XopuY`h@a`Wx&3&`5omkg1LQU)6Xq5&OWtX3'
    'MbCYL)*nf2rK(;!Gk6}o*Up9fX-7DIL&{a3+4nATh_Cr{YLmc|@DOsO_P|@;=4RycRNTWOlMO4i!>4|kfwi<gEJQhy(@meO-iACa7~l9{|F*~S'
    'ie}5lpugNPNj4REqRoWsb<TpL-t>qlgeRNN!<;=#g*Q?tBf8Ev(b-n5?x9)Lk*DAOWnSMky8hz+dyaq#<Mdjm&w|?qotQZz0`iRSD@5r*0Fi;+'
    'n)7V@mex_(cO{`;$<g+Q0nW&`9i(IFkKCW#&=2h%zFdY(e=AXU*ll*)r}L3;`_}wZb)ye#(b!MM;#-3yLm&#j9|iOqNDO)TCMDsr_SQ4MH+?_4'
    '1IuQNKZ<a>=`FD_<-EUj#hY9k%#f7?W*|3Nu6YU1{3`lfvGb1Bo=I^mbowh?BW=fRjVnU|L~l8ymM0l#ZHnD2TXuEDTX(Vpev9yXqz>4ASH6Do'
    'Q@6>AXToovru}L%vTyY1ZVHK^T5s-mdIciZuM8g#4ys!v)289MAqd;aW1MXkNJ)cFboaO+mDLJElJ;)R)y0vQBN=ury}k224d?5DfRJ{Z9d|no'
    'Rn2Y<MM*Cf<ep(GZGil5^>~n(W#D}m3AbLsKd(9Z<crUt)$sUfw+=B{$#KS~MQvp$Umd(=b>0%!$2%)*d;XZUdYzBIm!|gTS?-Ho<RGMRYUWJI'
    'wy30r7FCScR++6m^5|Y+)(%;RA*rqT{4gD!{&JIrokYX^wCS}Wa(B7x>kVT)Yq<N)%=VQhU;DexI|v<xVS76lhaPFM_D!rJKqtw`ar4GKx7d3+'
    '-ettagci*pT3{Ic<@eBb3Zb(IdRE7O(9d>~tqoU$$MijkrH;!p?wDVs{-?!emC7qHq{F$BG%rkCwHtf?{2W$GVc^zV<H$NShgfi~)_kEWB?^`_'
    'zWr1A$KjP2I`^?4Z~QR#iaKSBVUC9zLR9W&BWuV5Y<9`(#0-|HbJYBH;>K9}%{~}EFRIaB0{#p(w_qr3CsDB2atsHhBI$nb{jM`o-&5avFWy-V'
    '^!O)21&qk8XNPTjN$d+`oKS;7<#Ij^UZZ^rVrHHQoJV3$4BAqZGey@V%8fub1iyd$+<mzZbBB{}{z7}Xbh#O|xX^JBf7doatsd#lpFZ$|+<s@R'
    'Siyy#IG8}inSW6IXon2B!>rb>*~5XBG%IR%qs64w;`noR?bhl;=tUjEXZtX0{-uU1)m^V)k3Say1@+6e*EJHjb-VBT&)>;=n5RcuCc|rr(!{vZ'
    'Sns23yrqn@n^zi1dTU%?&09mWlqFcaE6FBD`M-Lq7E$)tMo4|p(FdnnCR_&}N^QF%<yuj%UCbSocWej3oT$fiGnBvLD~OA)ep2T&+!N@9q6W9?'
    'vv+Xp;}VcSWYJ@IX*zNjI9~f8G}l$BovfYs%4M`ANZp5~=Ay1AIy1S`%lQ~M2#0z*=q1%tac$S4ZI^i2MA$j3uP3r|qPe3c*1L#u?T=aWdhJqo'
    'rt;0wExELJR2=3a+E%+fe{DU!t#$nBxgx(mQt6ap+yakVE!i1vHB%xh6UT_p5ps*|{IB$$UGC7=M>?`knm%s$=r6##SmSR2-p(=y#ZOf5C=?H?'
    '3)=cC%5Nk8cAHmD?)4*$D7J|tk=wOZ%m(X@Ga7wU_w;Q~xK2^In*cgaUCx;3ldV6UN%!a6-Du8o*kLI3fKZU2W&R%Wf(|#?HpzkH4jX1*o@%Ii'
    'H4Tud)Ai{)sn(ht)ydy>S8|AFDXg^*&(t}g4t-Z+vx0~EqKn$U>+HH3^1-2|&$&;1>~MNtuoYAlp@Do5D+@0B%+*=26N<7v(ff^iw~&?fm^`wB'
    '#{AXe7W3+OD{(yfXz!}+_)^>Nhnpcjr$i}f*Uvx`s4g0b@{M=6p&R@-?@kM1Af7^_!Z+3(%G?jp(|sDQH|3j?PhKI`h?1L(;yyh}p?I|Tc!?>j'
    '$=^P*Ql<XppXQ{IaDr0fSlZ2aXuffoX9Y@QZ}5Y==r_fhMZajRFEH~Gv-7H4&ZYspW};<nF-jc&n(jAAeL}l`yfjnS)t=#jW%y^)iC4|A_c5w3'
    'nOOj&*i*lTJovWWRGEDmbNDa~D+xBGAdb)hcDsGQiJczx+C6D$9P0ZEFlF}>VZS_Ehe_>3oj!AUG;6J}xl@e>51t4b#~VD3k1Nj-g3Oq@Uf09I'
    '*+Yxs3qAopFh5M%dNT_q6aUW(3G32Wfzac<YSsypV^HQEk5&)7HT*NuVtp<zFkr*rjR>D;V`eW2<R<m{iBS#ISu|`dLU$H+9*i;mY!cy_15jA4'
    'llbegX{a2KTF3EgZkNzeB)X0I5fKQ!Cz-WukFe~>)t>5l(_5U~tt;(R?p()Rf8FvMu8|X5b9{N(m;DDtoz`&(fV_z3%6Gv^L|R#-eD4P(!+B^1'
    ')g26;-N~umK7H(JMD;&HE0bCo;N8!J0Eg;k&$@~(K)d82%nWQd>5|tlnQl8<tyBerKeomKHuQVvNo~1j44LqOja3zspcasHfDxlnpLytUPyC&c'
    'zge|5RsK@zpe~7=11}XG$z*qpW~PO3uSQkJ5Vg9zYZrG${^gfBZS^}zsASb%Yw}=D*RfoBbsl3$A;nH#e+6xi!lFw~^uv-Y$;uTP9wA*VHCi-g'
    '(kC!F8b3{5P+Y(ujaQ_1-9B5$Urz}9C0t72(z)*;2@?8~#ewWRRTLq?E5V^vhOTX(gU8RoL2$fa_HC&U$H`>ai~+^*b=MKM_bva2V99dPWjr{^'
    'H=7g&w-?uSR|{+~Y)aAv8pd5~zb@eR9AR(G?uebBW%Fg$r|u6!K~%Y+59B)r=8HQ}@n(_J#u6s}3Wr9`?EOi&Y%`zAWZa)#)EaOeZ)Wo7Quz$m'
    'RObsh#y~<_qE*zkZ@^SBc5y2{``NX|H^)@`cAh&3eW`U5C0ni&{n^+U>3Ow=O}$U5Y{yy9Q7|-ZImCBb)dFq8{HdMbkEV+SHG%wHauZkj8=Dm)'
    'i;=qYaMyyMd)%5-qvk;ATN%XcC0k-q06d7p%Ge$q%_a_67E`&~GQBt%XR^Xv@q~Mu&A@vHa=Y3)=KJ@iZLZ~Ugo|F(i@)P~Umt*F)+iniRUV(C'
    'iys^;F|lNJF{S(H`&R4`(=E1-^y6oNI=*hO(cxK3x!)8=?fdEJJ;7^K4DQML35ibz5st6C)pf&jz$Vi-*xlD=etQRVT`aJ`>E7H3c+tqjh+p8x'
    'G8|YWFz`D3u}@_UrFyB%w32ss`Ln@_U2*RBu7}NS)OL607X9wey6;-#zb3*o@BJ~*oqUUB8QCzW%<r4Zx#@d$uiL<s8a?Rk#C*M}cW=+u0uWmu'
    'KR>X}O5Y^s_Mydg;uxP!$ktWPTRo5?)defm_Sf?ZP4DVMUeP-Xsgqk#jFgT>;9Y0{kzQI*=jJ%EE|dBe-EHkX_o~nbor)To`77$iDjYA6Hrib1'
    'U_UfKXYjBZ>(6*zX~QS)HlrKHR0{@+yRzbrNCUsy-{Sf9>ZhAD=1awHQYzj|4%F|o>$u9I7F_Ek6%m%L_T&jFt~+ju_KgY~17nR4s<_k)2Dclr'
    'tWN28SKIrC1UoSD`ewWo;LIPZi|=xLd}UlUC1@4V=S`VTI;?<HA4g?j^gas<sQ$VSHLZZ_iuGNrkfh#&XFl749iYn&+G^!MDp3D`YAfD6FYhLe'
    '`fnewx7!``k+l*onOL!7tWMr`v!$lW;C0&X`EhIhsT!ZYAa3#A7JKl2UYr%=zMCnRA=@=iM6>BI`*<D9+OMKT{ps5TD_7Bxvl{s3>fji6ujKX-'
    'X-no+5u~}g-SyQtRNSOh9F6m!^~oMW*?M-7fqu$%^!ZSfvNkw3WxELveVM~hI0VVTmb*i<hI+dJV+awc!Fgp(C-Vm`VIymR$z?jK_qrVU*NTaP'
    'h_dkBzMZ>&J3boL%`{2qjh3w6dI4au67>3Gxo-{WJexG<X1}u;^8kFzU$58nL;r!x6>xi61>NuHars2EGo~p|g~B+drc-GPHx91syA|_{RaQNk'
    'J1MvX6E@xxU&rHkS(f^_UfMce(l02y4o?y)->3WMbv19p*;Mu`wV<<nF$1n09=P#lVGZ8x*J8T!oP<~&lC70iwy7HDrq({hS#2Yi2ope!Ila5H'
    'M=iGIj0~fv^lZ%g@I(Tc0o}_;L1a(_85Asr42Nd=nEc#S4xRig_g2<%ezvG4dM(F0{#}E+XQo$W9^h`Bx-&3Z1hycRg8HczI;mi$CibG+uKjk&'
    'eKU%pCuH?^x4A&kTd$E?*U<#i<r(!lT-ccUe)@}@#c=>x+cdWolsmn4khc6=jlR<!mq_h!>irs0IuSQ#RI22wpwYfPHjDk{F*b@l`e5m}8IRj%'
    'IW=ALowXl}SCKw?{N~q!k3A8Erw)OUglVmg&LGe;G;>$h;8Gb?Ci=B{{T%d1ySN#17&||<{l{@g08jLdnrSN~Dfq75XGb!~@#zo@+(^Crb!BC='
    'L-)|2DFxm0p~?Iyf70J{HjCb__D8|TpfE-X9&DL5FTYgk@9yiPwfXnMe)^1b<u&}a4sqQ$)t&eXPo-098`RLzlU%I2T6o=m3U!@_!t%Mp{b?wO'
    '1TOw@@#nBO0ou9jnP(LJTtN|3O&Cp&peo$I2y~&e@$~U%tw+{++5%QtI&TIEXG_!lwMx+~y@91v<KVqo)BbO>v8K{vDL%q$)Fh9$8rPIAjcslv'
    'SVO8a*ZcAEXpy_sdVTHyP{-%nrBYyvQS*A$Yk#hs+kG-KCZ{f+MZ*CNDMusdKL+ZSk<3%ZVXe+V8+F`}%ObHk>+>z`7kd{ze`2=o6!}iyXO3_e'
    '%FcYzpZtu)!-uQXsdlsea(~~XgY`lHaN84|Pa?Vbngvk;?4@6eT94*{d!sHu`x1ATH}Lh_<yUVibVmY0k<npZxx6oEAE7FZcDgimek-VbWJny1'
    '9H@Q{ck-FZX7cU_j;Oo=?)jVV8yl!CNn9vyrVn=gWG%OSqMi=1U7n6BsjZP*j1n05rKm~aZtspZ54ZGV@*Wl3+e4Nk+S0c)zGUP9<ocgCh<REd'
    'lfd!Etjr|WTEJ=3COK4_5<><rj|Z;XYJA$%WHve-%hvZ!+mGXGW!5iUVDy?RQ|wQNmI_AVd~@1}S$Zo?<iM?j(*dQg<rwa+WbZ81jCC+sFw}~U'
    '4*1ToKS75)j8DL%j;<i4ae*YfgV%a;5l%TkKUpvleWvVza5wn**Sb$vWiz9>v^DF@%iV$v_|3^1Qj9cUwa;;M2Ve@)$Ua?EGg!<5Jo-6{`9``{'
    '*ui{yc0tc_19r8mH%;(Z>(OLic~$nwP!0}FME=6nToI)@ZXe4Nwno4ulvRkJrQqhSk~k{up~4o8pFI<%ZsnK>g61_jkLth17S=J}AqUawFGM#t'
    '=cg+0ZRor!#9%?L&}s=<)}(){|IWpmZa!8~I3bGQ*>DIi3*q*O`#SZngk1yTu1boT8A=!3SKy{8S^TZD{J?o7-ldr+F26jz&EvB+!P(ws?7+hm'
    '(7l|F-&9(E)uO2rS@5|md+eb(?itLVKfjY=)h|?CU!HqQS!662o}=USdX1!==en0`Shr%c)~nM?AjNQ>udIN*gdOrTHjXk0cn;%fB(~FQTQNp('
    'd~K4+MFh53t%odS{q-~S{&G+&OAddF2PZo=SJfluj`-t(V&%?xK-1KBMm_4ScJ0sEpTp5`eXNLy^P{hAU00u=SM7Ez3F9S!Jh+wLY>mx=KTsEc'
    '@nWgMN3#7|iP3P<@1lqxVw4bn9Nv7#r=aHd(ucs|6${RDwJql3Bf7kwl$-tAKY9SCB(K)JY7ZK{$+mGrFRjkiYktW-&}TJIobfxT=mtMdE)7ig'
    'l9WdO<SKc+Fd5M83p$yEyH^PI%$gx7yN{5KcrirhG9(>(#i!NIGdkNk#E_lcv9pjr^Fos!pK(fpe6m{+CQCf;3sGNgCo7SRLwQu8G3hqr>@)u9'
    ')hv45fRK0du%vf~r?2UYY`?p<%=+{6Ub>$Y`I}MiJ|<p-|9Oh3o=@2$@uJ)Rd4?Ikcv@+^ufc-inw|M*aTx6pl|4(lf>HdY_)uM7*$V6#zvzJ6'
    'gb>%6$#%;&3l)gTMJ86`9wwX#viUXuq{ZsFTkvf+v>xy~+~@fhIR)y$zAw%Ndx}xY?)&e~JAUL=JZxkNJ+41JGq3!jb98JwL)*2gx7GcChS&MA'
    'zezixd-nt|nCPVjEb5)sb$f2h9ueThTb2We+a<eKTW{1t<5y$z@8F!NIzI@P1AgE77F8wmnUyzQ25&&s@crf6lo;{zym?Yr<IUC7Uxa;dl5RXK'
    '*|<!HxC&r0mrCqF)u=|qH%IG`o0G`0AU4{r!Yst6aE+(^9enF0CUJxMkH#8O7Grcp4OMjoV9_aCf9LZS7S^&(00RyS>Wc%*fcoz*T1q{&4+K*x'
    '?_;wySm8+3hPaHkI>0Q`@oA4j*{>qdSHBZTRQpnSNsazX^|7hborQzr&$yji95^9|+aEp6zD>o78eInIaN0LA9zkEq^`e%KT0^W#j0ycVLp7kw'
    'qn~<|%8=iFP5PPP^=C&VX5c|J+*Br=jAo0@rjGdxx`wQMht;39?eMWD{f<vL9L-2%=v~Z9GN0aW<27kZuP|@6H{ZtUPygic(3?^2#Y~vqz}PLs'
    'Ma&V=<5G#^I3wj_n|+ZhN7L4RYY_L#-Cq#STt|k!9?#tnsx<{A|KTh?u%$O9`9*ipN8mp!!F8%xSDKP1M;R=%t!ldf4Q31sr_fv+-lo{=IEXH0'
    'r?oxo-n0#`F4N!~+OwTbx_}R~&mnlRwvB!adSP5+X(L}xwDW##0Op(F;>}$>T24Iu4YVqL`ukg_(9Elxt2_Owc(2zZljg@3AG-?0J`dBMir$$D'
    'oR5wZP!OUlcgzHD;)tFg%i4M7lJP8z&L@TWt&B5Z$$6HAM`6`mXfjrLAW&!gp0NTgInHs=XkW-Zd+l^!OoWm3oo|%RYyaJ>r(M7E7!&p3xV|gF'
    'S(fniWABdFu9b_Q3`VzFBvk3hqzw9T1FLPYnWz)UTMR~im!r(BS4^?TnuXF&7mvQ!=nf*8Fj&vJVOi3DaVw)Q-Q>^#qjg1(Eq^|cj)2gs)JaJF'
    '`?TX{EpPU>WHxai>3R3TtRVvk9eOiZF4pzgsF_%esNwIqHFP-@dTXL0VIkC?EJnts;;irw&CLu-y+R&H18#7?ITv|};pD<`r<HEOp!DpvvA$6?'
    '$zGccBaV!Y?mX;_<-4nQLRz1cKmLaL#;cs91Jm0~5#_so8w<Jsd&e<*nqTv{=<5+7EuXEonf!%ufuALBhWg7iDW7U%quOZ+(UZ})g-$-Lusjx5'
    'Z2ll?47@3=_9@s|n3_O%w?p+$h+8rf(}k<<B7`5meWR3yl2h$nWtBMfq!GO{*8cYH&J@4LvRFRgL#FgeFa9+-^6Y)z$s&P`{iEGIwSdf3x}hl`'
    '#_fsBI>$CaG5_9Sc5Wf<wy^THi6R(O1CJSZ9bTV$tC<a+aakjq$F0N%NvBlC`gupm>IaHVzoU<q)V<A3Ku0nokcfpZ*hll_acU1?@%3z=Xmvb0'
    '9KMLSc43eU;i>mc(FOSDfnDBfB=TuE(qm=>r*(dF?SFy?Jvl(l#kF=3c6hy8t$w~Yh+cn!*F8Vf(%_Y}oWoXZujPTR1kt8;H12gkIuIhPSiAQq'
    '>MS?w>U^SEUXgZ=59h@XvC#enNZ)EH4g=jg?aKlmX}BE$lES_a?A|kW6LoGMZoB;^=xDpTP(Ms_3Yx;p`h(BHhD<!p{dm>U^l8s~tW>%CMPEa^'
    'y3&&p83Sm;IJL&N0D06wIt1C<{PD-uRYboPhS2Wv!E!B7N47hMBK}p2r&VL*se`0CU5A4e^*t>O)^Z-tsl_15p87TYF?_n|N^faB4rt>zdv`vI'
    '2H|a--QxMS<yRO9g*X`rXM3?8FJJlLey1dfzWj|fP7GSG%2?&iAcE%xZUvrMa9hzxcJTfS_5QsfSl$r~`p4YFDwSn8m+Mh)>2ll3^2<GEb(N^h'
    '8b`XlV%-hjIKlVXE|6}YS7%NJ@TtOg2<s1T@wTYd;4{9J`%!(`1kCVB?My!x_LnoUybiDQzFg0}%f118zH!jM4lU)Lsz2a0TDZnwb8U4Sy8G;*'
    'K1DKf^$Fu`y|cG_OOto|i;_P%@aG55!To9fTU0ixq^T)(<Yt?jaM-6_mt0>?2Z$>b;Cy@c?7)jMx8K8nW!~}u^A8y1Qdt&OU`2&Dpl&I$-Ez#T'
    'OS_Ivn|6fDhs%(Rw7%ekgNcNck_4d7$w1<I8>NNs_lt!;R8kh$<os{0p-1^?4AJj?wAl`;eYABxpIbn8aNRN^_ARRIB%xr6p1v`O9F*<(b6BnR'
    '=n1bX<-2VXX2sxlom{p?SKLGYzDjkWDwwXV#&WgS|0dCL3H-Xm#QB)E;<F-HnWRNvf(}LRlZMrjf%Z5MI2ar$i;nWq>g2F?+a7brnnCmS{*PEh'
    ';E?Kj8x|Ry0@lC^o&i5fK!0~+I>@%?M%No+ll8b*9`*hnG#hQzlnnO+Ob2JcY5DHx-En@-aQ`0HPf}ykEv6Bc-G{SEqYv<c$r+<K-Q2HBko%>Z'
    '@8~+Ruro64-s=Keq36fC!*IT}|L{?Yf~LJ=?(y_3-?65~3~+okuk3Aq0xoK)d=*cZLrO*aNani*ciU|$+ZMXhDx$w;u*_~uhZBKVIx{C(wYxxX'
    'We)K|Z1bEueoNkJ8?|0j3B)fZ%9n0`RfMF;--k>lQDX|ShO*eo;^Wwv`<iTw_e|5E$J`RZ-Q+^nd3=7~;~QLDs6g+y5E~s313mb}zTebvxTdBP'
    'q}*Rd9;+W;iC_f7Oo6*p%@{<9W##qZp*dfuI|E2n?hr?v<Z{l6QL<0_q_+cVQ~*@Y?cVM39O1dP-9LflaCYp$3eyn2Ch_B#6L=lW*~t=}^p@Rh'
    'ifk-DSS(1c!cP!yZ~PgBn5$z+N-XXE#ViTjHBO&9b*V(g8ycgv7Jm?LjmiZJz7K3sL!*2)F*RY)i?q7pw=Y=zcZ-UEP&sGB2uoCHjCM%)7)`3Z'
    '7e89^!7Q&5gIuh==Q8g%dhLujdDr%3xM#LSa{WCjosO1PR#^n_r(dHCO`vVXefV&i_qWZ?dk@UVC^4s>Xi`f$6S5{8d=p&PD)FqkK)*dpwOn`p'
    'd!$89Bj0iMD;F)x>%y!juOsGQv^UrAK{pUl8wNlLWecy_9^`~sy*s;Bp*DfL4UBewLn;o;Ptd#C;aLm7okpjvAFK1t<FNTx959SAhsE#Iel!Qm'
    '4c3od-O4q0dvns5zvOtBx8uih(k}E)^%R;ObL_y?OKy}-HJxYGC)<<{%x^8W`=jo8@oh73%_y4yjonF_F23r>sy-EOKDva-Z!($>^v}bQy8DM;'
    'Y>L(QFmdgqv`+8iEOYYSs#zk10WTY8TAjX+V)c4ltWRyLgkONCt>P+5Q~YWM_{rvk&X*CPsb^hSu$Y%g&i9#`?P@N*28Z_QXQ%*|(TZ}ucCSME'
    'h5qI_(zbun{bk6-CWdbCd{@1E+V3lMBcvp#v4MB@IrcRa;Xchv<BAWE8EYZcI=|RdAGf8U_SZ%RQhvExb^)5JpPfj0pabu;_jhav_4%l&T-u$X'
    'y6@Dx^{*2)S;Z_p>L?($q18|Rv}*HIsA<0KerKI-8jJJ?t#q_v{+AiI<6)ckgWpS_Yj_Dzi@`}gj4A+po&$y>uNUmt!g|Q5^5|)|CpfyKx$q7z'
    '+9{NDc`GKSA6N6Z9Iy?}X<grCKRV2>mGZrPIa~w2^d_{ksebL*D2$h1$vI2v-dW;%QTyVVYQgFO=a~b_y{8rP6qy~;!EF`CujAcrP%2>1sZXoV'
    '*}T#Kt3#kAi%kfaX{q0bCKFIj%wbn8IAL;PomU<~<5TCmjc*s>2{!7;9n^dt?d8tne6O#t+|$ueFZ0^C70uuha26L(%<ilE62fGWITypXokgw7'
    'v=O|>Hz2l%`~dUE%dsTB_VPF}`Cj;FA6M4;`l+t-`s7UN#n8GH?DSq~XBGW7rAC}InqV)V6ff+&Qb*Irv9i2efkSUqd=IXOY*j#P*LxSNY1Er5'
    '@^wxK6TdeSRk}wsQ9Z9j_B9PCyHoYwzs2D=QPNSp7#Bq7f=kTVS6*)PfG}PG`<}7wj7nuV`Q=P?J$|1bhs%p>&dj~n19V{Y5g+sS*z|aMS|`^T'
    'h3v?t<I5QCi^&G+K{tQ)RECw!QCRbyb}foCwFwZTC3!59&Hz&8f%N$TqyAu$E{61xsoHJf(OWMjdZw0C)vQ0Pdz)2z_ls+PGOsbVlVCY%JlCAJ'
    'vyVubH%CLTz5#F5tAASPannQk<#~%MXY}8;)9qwJ+UhLSR+DS$E3bO<4m1XsWFM00HQ_P+RZ}`q9E^rOI~ZN<4$d_U$9#>OU48T%14h$L_e|Na'
    '`|pMGQ^lS*<M{>9z43h2Jjz|CF<1i6f&SW^Wp!x`i{bIBZKff?g4D?mMc}?JB1zWZ*euBz3eO+)#@J^t_d-Jw$e?y@uLylX(|w|OR?|6nVzfzH'
    'ckyI9^RL!p%c?ccOq|5XJ1SJoj{A@7ib8LRPoMeW@9qgpYzntMf8ww!RNbjI+7GrqIYrhWvyD&Gv-gXzRt4CCo5wXA3<_Z>82xMgVqaV4jp$VB'
    'Vect>r<_&l!9H|0Ti=p^nsWI~gF>#X{4_%C^Q|9~egBTq$_ssdCvJ3JtY(_3w3?mnwDo|bN?s4MBN+RaH!U@j!!4P?Sz{Pf^V3f1Kh~=O`1`BC'
    'JObvi`94e#B8K#xBn(*egA=E39rWVL&_)JDly+ueRzLSuYZRQi+0aQ;nCXO_NF(xQ<y;IV6u&3~$Ss${2B5;g(8}ZE!*$2=GQ*v3b{apSazSgC'
    '9>I8j9IzF%vSqfI>o%!*pWMC}yBd6{-QXwLP%ff16LOQc|J>>LytsflY2lZ9gxzCx4Lv*1s;wQy-Y}is7#eTA_*cWM=gJ5(+KYA2zEVyVJ9r+o'
    'apgw)Mg~0GWvkso4SM@8GO{Ym!!jt`w@Hm*SiSZx?1KNh^Ss+nk4Q^xG}(lysh>u$dIQiY-`UT@-23gXYogX(o;KA+rP~;i^Rhl7R%UZI^xh?Y'
    'ZQhXD_^-osaPaAL0GBkhv49=Ov2usaM1Nz!pd?bN81?x1SY@*spO`YQ_Af6&*_rv8+qv^fd$dc2zc#Co)AV7?;q^3dgzLEJuLR{f1g_?{A)ZfH'
    'qc|y6dg!*SnFxdXmt(R{>oFbZGuwI>H(}j@P9&SZl-{f%izi)1O6RViZ->|Wwxchouh)xPJ!ji|yuOup#m;A0;FtYDk+(zk9XFb}2{>krh~^Ba'
    '#Qp1ewQ%pxck2>wvU-|`&pB_y`cPSpCFJ0qX721B9og18*rz!<H7Pukuk5(C5-zP}Ox+}OmbC{H&66){4H;O7@9gDzt>64WcdFYN#I5bA`v(_v'
    'eX{8o0DM_|32>=vGeE$ZNmJQK!*te+<>#u97rfAUTldfKJ6LchIZ&P!dEdBOxJc|BKPt;v>(#ndtn>J>!>*R<Rj$S@fXt#YqMA7UzKuuE-HK9@'
    'u_!$F9BcmRtt9|EV-OJ9`p}IL>s_|cIH`1X#)?WYtK|4wK##PFp8MKHUIX>(0a(ToM`%cDU93iV+eCQD58D7_?S<PNVFv?XU*qbcg3Py<LkvGk'
    '_2rE3c}+nOmP(h6MAE$87Fu?ylQLa|RiEoL3MKUa%1j-9A3b@oY~aDeuDU0dQ#wGq3QwAPw>NshOsgG0kIqjta=cyO8v)=8?<T?3D@y}J)7IyU'
    'SQ$q1j9h*yoVHm!k`=Hdfu&II&9~!@=k6zu<uO^zZeI-=W=$3pAjARSv3SXbMtvx#jsCHHBDTzCGRz2^>wNIRdHqc8)k#$;kGb9+tPlgPez|p1'
    '7zEmpQ^$I<D3%h^uX>uaKUe<DSY=>CX`p9&k|D`t-B*~MHZ&)ZKn1@wfm?T683p~IktJ-a;si-9-u|xD?ikIn@&JEF9+84jD#Kg48rD5IdMD}A'
    'b#c4~)t(Domf3H*du+d*wW#(V=UeKq^(veFv8bc2LY89YPQTWCy6rbBKXoajo{wcE6q%K~J;Y7vWL}?>DRbRvnQig8p<PmP&c7-3&yn9{`&dil'
    'ol9AbD6F5V+7I0kf6-POMz^Fk1GYjld82_RV%<fO4{mW+I9yd4KQHE#3W~#<6Stk#rabgttIBCAqVF3$O{c2Wn2vAz!}s<0EaPcXcxb12wA0JD'
    'HJ?ScdkK^gtfv`BxJm&|h^2_-@2fp9TC;zLx>pC__?%9SSw&>G&K2;T$pw>whmT@lefVir0wa5!shK@`DbQ*3DIb2o5-jsbG(KIkJvuHpME|Ai'
    'P#*aG)^Zw}2-NH@c`&0aeG||%=iYQczCd0z{BG}rze?lv{SIsc6w83)#)8sGk6zpk2?td_4P3y!ks4r23;TTdvBc7^4(UnT0TfN!>Ub7-a0=No'
    'cIAC1;wmGB@IHXXV)_j)BOY9XM`NJ;uBTngnO+?n=7ufpBb>T@Z!+8X+55%;p>7ACyo6}(Z{&85pN!v<*oxEldudioKcoF+4eym9;~EavZ^Ri`'
    '&~>@rU3t4Wo6v~ApY#X$Z#mvmRCk`w(`8zR-`%c-Z=Hf{DbQ!}GDEzJ8{0mX$mPLXu6^R!TN-<E$jjnP4|n$xq=u04m%)NOa33h>%^0I%el^9^'
    'j_=iMG#{y9bTnF)F}ZJBhSL+f)7`yA`QPA*-h>M_CoP}>aekvpnaHeF(|hvc2&b!c->v0WGh~lzCGiC^x)cL2`E6JA{E#!5e$&}OBVDh$&P{3j'
    'ruKE-Z_7?PtB+!CS=ASPlSsq*pLnlp$;Er=*G(UEf_kEkT0L_7IbS;60l8|gH~UF`M#YB6qEVcs1R(+QLp0joXtlU$NXfK{Fa)ia{YE#rP`zHi'
    'G!;GSbykqhD?_iNgWpu~U)PM9>S6!g3P)mxGulA{hocU@dCXU@4K<Jkv&+w?^K6)6{v`)(l&S<uTTl1oE$l<7Rrbg~?A)iG;C06P$1%0IqX)t#'
    'SpDfuEM%&p$l5KuJGb7Q-v^4NW!;(Zmlt#-wB;7M9vjV@-<ZwHOc}bS+zzs2K0iPA+uy{E@eJ$_qs}8~2@fo8C)W34kH4`2eWiJQiFK%G03cIs'
    'dtVz<n9so0>+_{AQ+zM%!`qFegei@{Zt`TW?1t@xkd*CL(>vy3?K)#BqPQN?ZDzlK58k+#t+#z9Cwe;Mz1Qpba3AI~AJ1=-2mI7NMrWJP_gOc$'
    'lWpGuk`*+4uW%f2dqfpOL;7$fqe<1)4(OM6<hS?-Tw0Tx^V;c#N7$-{KT3=yLt9z-RGp&rnRQ17(+9NcsjVdwDD#`~24@`3?E0IrN;u-`RBpTJ'
    '6ONJ2d1*4c)tA26_~ae`@mD;95*G)xH$fVL%I^T*?q<}cHar*jq%m|iXTYuscdhF;j{bqk2dlCwx*0yp4oTntR;%5vez;p#Z?a5{LG#mm7RqCS'
    'Uv#TH4VTvZ;X1aQZ?B4e9(8u>!!4iAN9oCQRGTJYQh76~vqpBa3Jb1~PMeXoWI=N~vZ3zc8)@*%iEmbI=L{%mmjuMu^u3L-YTo-L)1kbG1I=-5'
    'Xiw_LLF>>k+3!J2j<wqY){ATXe3KT0TqtVKtnnL17eqaHj(c>@C~77dFZIk1lCn!#_lmEJ%k}G|1wFgICMFocY;oHdjYIWz+c44yZ`_2aM8hNM'
    'zoiK^-#$@_{voKb)Xvl0?S0(2hvcyt=XZU9z!5ROmra*xu7d^Y)mmA6s}1YVbvh6^aspIOW10>z&hp(CDTYwi*S^J`uY1BLxVGP%*-3|Puk1Le'
    'wpWRR2KE5$u`FA&9pVIty6Rd6@__IH;3RCOU60kg1AyPWYy-cEdH`nDI~@`E$*=a!@v7-d@pSq$U50&Xo2nnOYzrxckcyVW&3cdt^lE?J=;SzD'
    'Y$-;fzSou6(YlU}PaUQvrWKE-)@)ID!eN;0q-$+34=-0^BQnilyda3Iuj(X0RVYu`(a4(l<He=-IGV-WTV28;4z_7!tF6dj9991ka`~s~gUOa2'
    'SxlGU^eaky^vYU&HQPxrmKAJg__b5Dn02?xy4tQQGg}xPnF=+LN7B4;Yj&)D<uwh{ZywzqA1bjX<op;7Mr^+-#V-_`tcdpTz355!e%m<{_s3w_'
    'ukfy147}<&+>O5~YB)QFb4vcx86{yaWOyja#!8d$uymB8=EYy6-TG#s>_&PvR=dxcdqJzKM2_Wq4L0sSw&Uul_3FwLH3nB)H}u5Hod`pDe@{Vm'
    'WNWvHxk@KZHoA$ssLqCq1+!kLnckp{+L@&<r;>RST+6{v54QcQZMo%kiulmJ|6=GH8XWc0>DLPVoGB|GuElH2)<C+3wIle|J!`&XYFf^7Zn4@g'
    'xwT`$4d0lM(%8H8#`Z%$4_+DV5(9S#_r8Ely}q*pcKmRt3xE2tGUH^uAjbjKLPpJI(f{;!z_1e3mdC8WgL3y}QIbmCyiL!N&ZqSUD<_M=^E<#z'
    'f4vG-<6Q+vBw2hq&hPg*G2SNK!doxlqcw5hE6uWa_dURT@s~yV@2!G*K)48H!@}Vb0_X2A{M6j3)vVxBdly4^#a%8Wd!{*#bn;JwYPrpa#01Zx'
    'VZCeqv2O)SprmOAi;2pnk?{d>?cuXrFr8rQI(Gr@H}AXqHoH>{FlsX6(+M1Pv|$$-z^nS0enpmh5+d9Qkqn}5;SE;(mEP2@^c3{&{O=;w@+Ut|'
    'n#SRh6H2BzcC-8mlq}v>FJB2IOaa^bB@K2BzR}Bi&6rDS>wkwyomBZb7%6pNGS52b)i@A~L3_Tk>fHx>bqNJ7h()cVaD94Qo>zbPl+-zUskJZe'
    'gzI)C*d!Oy0Q4|KsAuQ<m<ebdd~q~={u4)EPB+Ubp(JMxLE!Evn4y!0>3JQlwUkx%U1dhKbf$IAdt<J?O%2As&`z6`m1e!!Aw=j-6yv`!0--SZ'
    'Ea!>X>+_!DQsoQ1b@Dxg%5^L-so(Q+^!m?hK;qJ>*!%mA-MWFlWfkhYifxG0fm_aB0s3!k{B17o`UGfU3T7e2%&ZdCP5EoMTwYFTQNlyweY4Jo'
    '<LP^nxA+MbW3bMd;3|%yqL=<nqQk8GCLnz}*dA=`9I)&nq($K)jPR?0)B3Yy+;o$gKTF$<+BdlHKwT<{XTDopXn+L{{=zu3<=XE-dzO>(HQNM6'
    'Ey0uSyj=`i82CFk<Z<!d+`jku9@ERsm__X)_g9L&I`WY=b5g;3^rLzvdd^SlWB&eJ=U{#=pO)ztUOCb(MjoT+(0#15%B9y?_?1n~T@Rnrm<@B%'
    'dJG#DiAh6!`mQGJk-EQ8a}MJ7{aS5~o&r})<qBPS;r4-zH_=xdf{|TKNBv%ER7+ZNY4zu-P7!nU@7aVtE*~V!s=@pXcrN1%a^io-SH586fZaaj'
    'ht&Tq{gJwcbSIn72X>zDclaajsh2QG9%;kr$>ml2wrHwynF+I5VTJBzq|7FHdZUKRS8|9p5YZwT<C%lPyj-&%6Sg1g(Q)qw5!!!E)-`<<h_7hB'
    'yli^U(k1Iy_q>i&2rULD>dScVmDAb!g0~S8a{MK}<9UpAo(>lPsJ9+<vf(p(f0dn61MT(t>V7_xWYP(z{hNi<qu1^^2KqLjEXiL}|8+LQvjLw@'
    'PkKJsvgPj8uOFq)!cxu^ZB+C}7StLy3hnzJw$5v3Stx;`&q7cm8Z&^EpeP6;U_p?2p)>^r5fB@w&pzLOImz6g7(8X~wGv82vz?_0a=SWKrZI;%'
    '$l2R(H!ZK$j|Z>5uw~dC-Fc0yK1ezC>f6a9aE)wUT)c-KeR*KP>|SqKK0JK_nXn7}8ZInq2T36uphq0T0`x6MZ(DjfmrLJOHLwC}^0o)RCp%y='
    'a0KnBZO+%Uxajo?-QIs|p5(dvcj)evV}<N4cUX89*m(KynN=E2I_k*^lthtM-llQbpS(3R)&eKGzsoFt(Jq%6#-EPuMOiBi!@6FnP-}c1M)x_+'
    '*+Ejh`Xg6(6BHL$$==I4RrYqBv|t~6dQYRg*tx=%>$bk@eyfqtQ4K19VeHTApJ;<gj_e6;F5v`rH|V@*E{jCmfznI5wO$mn&pYOTFTkrKKfaAw'
    '*;Ve(Hn%um+RpuSs2{4uRt3nQELO^EuJu}m<(N~w-tzidx6$pOD2<qFS7Fnr#*nKL{6KVfHY025y7D71>Q<XTg_DpoBzYsV1brJ}AVS!3y(1p>'
    'vRZ?%dJ@AeLE=Yc->aY?dVC#6<GucSvZUARcrW6^6LJZSc=x~!e@U;N`J#~~i$TtX)`0%o6hCW}g>&H`{5j8ab{!%$`xJ6v%5eq(Hq#NcwBD7u'
    'vtMt!dnR`NfZ+V^YonPs1}S>?djqJ`*sD*FKP4og_pQ7A2v#Yt#mQW0zmMi-ew8BtnwrtTsVz$lzvj*QBqkJ<wxdC}xSZjL)1uzvhk4Cg!)}W~'
    '5_fv_M3FmsbJQzN$^dd5rA9E{>9l<P@+%!IE&ke~cI23lE2}@$IYvuh!+7;sxPx#Z>#!|6w5Fp3puE1VP1W}!>uBNS0L|;v2ICqfmlf!o`7uE6'
    'aeoYE?Z&#`>;v$uWXn<3kIS~Q%E{quAua4g1?yBpdOan8oHoIy?E}Lp%*gT#JFPl1dzY?gXEZkQkgUBOc`#1BX~^^YMPn*<Mp{k%sr;dw6YOt1'
    '8Ls}!jIUoGi!-?etNft@wHMXeby7$2S5MHn*HUUx8ZaJBoa;LPC^S6n&l^|Din9EW0(gJF^=Y#C-8N4$XS{4vT`!7nIr84-7n542;<A0HJmaeE'
    '<~-W|@Y+B-5y2S#o^g426I;uadRa6Xq{T-tp40r&Y~97Mh&LH3jE0Ch&Nh45SfOtH?i7jlcseL{ptn9c&#qTS=w0ReHURxVI1=zL9iAIkbJ=-9'
    'P~GH{b9-ZzJw`?BN#%t)E{fL>X@9r&&5~Kx;7zz6HUDBG9}4m3Gr3<yvC$a>{e2>(JD_UWtWCe3dkc}#_f{mP8z_1)T00yNg2Y%RkbL@2^`c3K'
    'G`l$#xMDHOW4cUqtfp&gzuwomT8y3h`}4~s4}sRwZby5f<vWA|#f@2Ww3@bS{Z@+}aBs#h^w%F9UNCWP?bDM})cuC|2m11E{&~Cwg+fubx7Z%r'
    ')jg7lYH3veg7wm_jSHl%vCmVoOXQo-dtDR6y5rfGXe@xb?kcZO7?!Tk?rBw1#)n=oso*n&I$7#<GbsVtPN+;R`tG-XyOb5IX7utWbC^#;{pft}'
    'zmaq{J{RuMpE|_TDFk5y^g7cFCaCOT$gnkxI(MuM^fYI5(otUh8w$?x8SDaujgqtZY?Adb;mE%i*TYlXou_Q+?0cPWzXTSh3Q$L=-^T@UTxDm_'
    'BD&_B^7!-@er>fi!s~32`N10UM&kb2z=#7KO*cz;d}LP3m}1xa=GU}cu-8xW9FUsV_QQA~*`Rwk9NcdSz;yI7poX@);P>0a889sY@6obLlv94s'
    'w+8&#PNPxqxAbVbMSLwIqpGSnWvln56Ym>@*Y(|A@yp#-o=}0`=jA9n+RZ-YH0r&>k41EI%)AD59B+s7bupUX-uNi!Jogjopw{`;1Z*TU(S!F>'
    '^W@E~;gphMW37sZfjY~bPV7CYF|&HUl4bRBUEmAuP?DY9G%=ba=#D5;(blzwJz13#mY2dX^@w*@%&?8{E8fL>$Um*xPc`<*%{<lC5Qa|%@A-i-'
    'p<S!HhvQ1PrU|^$r3VUXq^+0vNjBUukJA;oD*~yMitXW6&>IA87Gg)}l)wxNyfwo?!{yw29MTG^@96RsU#->WJI|<jJ`S-Qu`m{^vs>nVu6viH'
    'Y4xGMimNV)N_g!K38!c5z#ZZP=SQD=Z)o)Gx&UOorq4P#-BT&rmOEQ~DOH7F8yez6^_%VKqrpU{CNZp`p?hYsy2te`v&Jol?IM4Wl;b83__Dfv'
    'O5?M7LJ$27C|7G%yHm|wgKhMcTZ7FHwKw~5d+Y%7i$^|NobO`-MAFI~nKlb)?zAzvMR&V{V;mIC#Ei6}{TL8K80x`(8b{6NA>WQayP&DP)ZU!2'
    '+z8u*?FXa;9cE9z?d949=h=I0EiN1wpuz03O8z|qf#F1AZhZO)>#M<fo=Tne&>~*1JKx5pmqp4dw*xIN2k4Ht58R}?<SQl_wN2|_3kLe9-sJN{'
    'zyzbg9k$-j&;3fbd^>b9joI9|`70@E0~A;PLht;1`qq9dI&O*k{cjE)ohH1Z{Hk{iAU?Q$>Vx`7fXpksYLf*EN0Af#tPj-r@Sw7V0O@`j(&9<K'
    'm185BG=Ga0oJkwH5>FQm(0X=}H93ab+jg`HJiCRhYsRhiWq!Yys7C4XRrIwSFB&J=NUM1*Kjh2JvKon}E!eCM8B?nOm?Pg<N^0*4?sk3N7LYSh'
    'uMQ&&UTe9>zTt~x5&n`Up3Cj<^}$4KQO=(uP;ZSn+CEb3epDL+?m%dWu0#}vqBykBzE+=5u6n+j@$Etb;tNay&d^5Gn5;ZY=`y|i{O3Kr_SLnw'
    'fMN&#c*9$JGm)n|2`Y~DI-yR}d%I(j6Nn`OyDHi38P?jad+4byDKH34>-2c!(lrYD3XC>1V~`b%Il5T-XkyaWj2~C-W3A2zoZwC>^J%($<JIRU'
    'I>lwWA5j#fSt|QuC1-7Cya+Bs&wJ(dSM?7q5+5=uNYq|;>O1=LtNfXqxNPiZI<ydxV{4`2=f-mW8|%j&+MJ>_U;w(<9_=dMaaYHZ_13(RQ{_(g'
    'r5A7SJ3W52!e~Kr<EBMwRpvH3INb2ygl`;ieGJZZKmp8{S2h3W0JA30fP#8Fh|DXZe5VmN<oBKRa@5>q{mImM`#0#UiQ`PV!wNRu&_51_YTFlp'
    '1`hD9Vs$}bYkfpo?&x`WC1%85BRs)skL|wxJgMFtm(i9GQ8+c-b1F=9fnllqlHrLKo(}85ymGaC08_^K^C5v%4@Y=yz99jIBL0Z$M39M!zUWxP'
    'D^aQ-5{j$#L>g!v4*px(*qyXK{sS=lhI?0gEfa4+{QjWznHgs*o#M8}TFs`@wNW=sU3OG*Pj$Vv`3!_l-)xcn?`zYx+2Qd2zqfWAZ%kwm?xKFP'
    '!-;8ka_z)OEB_vO0-J5E8AZ&Z${_NoeZOVL4d?;Ki+ZE(r|w3ojDJ@(d9-4)Nj)GnTwp*6Ul*5lIoD?V$!OdwZ<z-k-Zq)dH1}5!nb=u7ac;FA'
    '#oWkZ>rIeDqWa~ZzB6@tJAUO!dF8iWMKf+4ex}mB+jon{a;fD_1}L-_c*>Dm>)U_I(BcWZo;I6%L%Cp%MqHQ7V#@SSL0zZK0qOOr6NaD4qJ68('
    '%;U}MX{xa<{mba1OKhXmZi`EA%-<CJ4jw<kvqHqX1t9Le<acW}#`tT1Sd~lOLf^?+(vlf5t$p@Lx|_KL6Zgf&G8F1HEBW~`gqV5j)5gL~YnZ1?'
    'LOT7jyD1mqmFKdFdubhkKS3;;%4YQ*Q{!u@59yxtr%{Q*e5BLFnt!W(x1J1K;&i=Sz~iPC{(0h>C>K?)(>DZkEY8lmX<HE%f2q`hUZFve2W7%='
    'WqLSm@TL>HS$Fv&tk`NrP*C_rT}y<>yiNGlN}o1ATMFs`L3TA=`RW<L>C=_A6y5+pvKx25^<#hX#3S55p?u7=8~$fhgM4S8Y973LC~-Oa+viJ!'
    '8YJC*yG_ip-ia5>Ik$RS#dp1dQ(r_&`pK;(&`hzW)(aF1n-d9?ZmeQ%KAG3qz8`B^ZwNWAE}37W3jhPAt@l<@C~c%WCjR9nWY05hfM!o0VFZ8Z'
    'h$WJ09ew}By8wA-fPhKyaNjsS((doCZ8aDonp%|?^JHsQFt+i%)sFuD0IxQjvZzcSLo@Ssl6uEa=ZQV%K#Bh<L^pUVo7TI-&i02OJ@$S5rEFMS'
    '1}*jQUX<(nWU<YDKYDO<E9oA`{Q;y)zrlF88;e23;l<5*)2^7=sl~RDR(({o_H`yds9lML69ho(!|t1Jc*YRxlw)OG+r;B!qr>wU$Ma8ba19#N'
    '<#znk4sdsz*_1ec1A9>41?LX(?NE7T?Ung)g1sT>{k{m#<BP{hCF=6KZQ8ggo98=j@KA63p7Lm|Ihh%!hep3<_Zks^F1Ve4xt)1;`wwWdq=xg!'
    'qFo)RSbsYq4^QiSWk_VYHT(CD9@fy#CTGRQkrwJ7R1FUY%fTBcg-q+_{VXr}#j-O?JM3*LUCFLN1mdlg${foLJ`1R+{_%$^HUoYEovPq?JONgB'
    'TiWN%YRJ9Yx21!KIk9F|Z`*vu+`Bp1IwZ_8tzC2bU_ISvcKLQ~Z$~n$Gd+1|N!9fWWWJZ^*i>lD5HIgs=c4vv71(zavhjPT8#VTCy^XC!7;R#c'
    'z1^IQ-R`}OS~XalH#4%jbzWKTYn^(h&F7Y`D<Vu0$QFiu%uqURbp4wsSh@py@w0n))&*Sy;C6$*l$+l9+xdkAS$Ft$mM1v2zF<%j{oY&55_;a4'
    '!%ym4T(yG&z_3aNts1+gAAf!<*Vi|EFjtnjS(C7)0k_?E+Gm41dTYQI8V=i48q`N{M}a7<2EFdkbu+D^M{BSMrckOQSAZIBxj%{C54c~0ZD#&b'
    '<);GYa{RNmt6w_GyL6{aesi#;u7<ln=gr${R7{+{XuKicc#q<gN?zSzt#Oh5^3@rxi^WHEUvvds?E0hOrSKD|A03_QLM}EO-h5ckx-giYj}UwL'
    'k@w~$Tosmmo-qtCJm)UhW}X%Gc53P$DS0$k9XG@LZ*7+5@_3!SmXt|0`xsS#zX+ID9_J8_z+%P>&X-hjpfhu>u=E0^ut(oRUiGRUuXk(-lShPx'
    'O92J>@3v<jP2AF4%k0#Gaw2`|eVYBY`rGcszsme16FM8BVm1Yk8-+`bB;(qn*43ii5{eX4{GSV)#xpQ7^+fF~Y_c5J*s_EduC@aFiMiweC^`zp'
    '*&9DM2|k|v_;@pkwa`(+5iua)p^R2e(GN*>Z}Yfq5v+a&?nMh1kL7+?pNs`MG>}6zwX7Mo7@p`1QXlXG_-)n3z5zs_SLvJXsyE6JkxWu1)2`m&'
    '+uX%+3z#R@R@pB4qdH%0x<syN=)PI|ZTvUlK3!sZ{8plU=TNPtv*pp@Ppm3ht5fmhZpQ0_Hqid6wgc#PGhDzm;Q-e-*I40WaT;w(=qz5=q%D1?'
    'i0$p4ac5BWeXb*#vVk@a?SV6<xKX`u4#)3#sBC6?_i?IJck;=1KFC@-B7~^!lXk;-Ui*=DXqg%*s`w~O(d~kj*UIF3%Uqpd@h)NPhVHfAAD)*)'
    '%INVkpoBvje`-G=YI#q0b3Q7SLEi|gJA2q}LzOBE)$>1_#7>~zA1VQJFV$A^7c7Rmq*`9LAy)I24yLn4sj%zw$Dk3af5l#Ww*EVkH>TON_e07-'
    'zK<f_UZ5}7LnnIuJJ)q#KU3}g<lE?B@P_|2FZbB5uG{#>KV6tM_S$#iIWdL@*ZZ4QA4~0T^sv9#gMEX+XbK;9qxqJcUz+5c<mA;n)E>KYioE;|'
    'iUb1i0)VZ*U7<YC@iW%4Ky={2pWaBeVC5<pi0AkHqqZGDL{H{fu+cp}yVrT|1;ayoxp>DjN_5|)F*#w<7Z%fBUJ)+YbOTo1JV%|jw+awAmUO;)'
    'M?C!NMfmLqDd661KE+2_nA|Z)*P1ijh~9MkcR7_16k5L!5;9?lHginPqRHyV&G)s}c#-XLb0pU`!v=u*b>)}af}QsHTZj1J395|HkAK`%dz|Dp'
    'h8WY78?Eu_hpysxD4X<K?7I-*QJX-)#S=Q=#bC?9#FC>oyINXyYQ2!}_dJ-jjp)L>CRnfW1F~TnNlI(%PaXfz>#v2$ByU!h{v28`&tJ=!X!FYH'
    'V*1PJw0Jx|b@i4qUiD0U=Yl`Sy?NQF=2}UBm;+W)q^4^^2_$V<_zQ{o_%2en+Q*Xn?r-cjUhC3Rf#J+G_1#z<9=Q|WL26lQZzyyI0R2?Iwg~cA'
    'x-PZw_4=8nitN(`(|D{;8eft`a?hT`lU&8ypWK3-E-80}F4;G6MQ-!elQg@vwpJG?e#CjzzBQWlk)yH4UJf4ottowM9v_MqqOWR!Rq6B>$01Tv'
    'UR<Z_o%glz%Y4}1FijikOG)Rw1UCmjqV8`4<S}jJ@G|~$<cY#r`=y&BC%(71edxt`c3chipTi$!xvR5YAuCWFrJWA!9)tS27m{q(t~!j{8+YVG'
    'yy$@u|9x}bn0yT-><?^WLmr!Q58m7-zwgxsS=1YKeoVX{->VtFH@B@$m<k>K^K~E3VJj`Oecfz?ZhQIZ%>UeBj&|C?E+>wteB=IQ3G6XXMigkp'
    '%}<Ap7L;XUS@BYJ!-U)Vh5_ZxoOl}u0m)5Bz7Msp<So0stT4`RWRfi&#iKL4RrYhB*ALi@@It*ifo#CXyoTH+jY8nwM)wo=k9~rUxSsY9AE`qP'
    'UA$TX#nIS+t@onfXkkT1YBcV}C-RJjV?wZLOJlrOYU`^y*WeI1*`58$m9UBwn)&5qpn$PZMd%)}pZM2O82(L&dwwnLVa_Uch33hGX`ky0oAwZ}'
    'J}HRwc}+~49JkrQ)1soywzF7WH03jz3prNQ$p}VGEOr*<ez95$5kWR@J^gcTV$0ibvF3?1E%nybOWyv0fEGIWQqMA@kpl%6%m!TBmAqg-BMVTW'
    '(Jj4>7jv&euhutKpGxaXA*_G=Jrg%F(_cx?-Ytul_tA<YaV`Bk#v!uvt8Nr+CCeCs9C;qpA8l-pg{M0Iqyc@=RttPOE(F0oRv4Ik?W@*phFo8~'
    'YuEZbnv1nL9zVQCJU=g(pCs(B!&e;g2Y(%o`fW?6TEs2J<d^fjP)nte^niLctQO~aM@DHR@OpD<ig8_hF;-`xC}F9bX#nCxX#W`;QSL7=)8Gk4'
    'Nk3io_+B5jo;E&g;Fc;E4P(Kto2yy(foojlmt^NzdnS$?<@qO-O#i4>D%oyR=+a?wyC2vz`=J)SedMDfJES_x*Uwmb1Ecc%vr_sPzT?D{HA>Wf'
    'J>PEpsQBvknDyvPP0Q)+fKW`ijh;2HGI;>>w=+E>&jApn%g2N5;43;&y-!0pg#B+WCH;=v901D<6TjB%WjjS1Z~AF_-^MVj=l{+vEWTYb<q^8k'
    '-MTgEc$PNXv{QlP4>sy-!m4;}v>lhqkM3n02lcLt@T;rQ9_B94-e}Q@oz8D9yO$P0R-0WekWDb!=*99gIeCVF+Cq@cTlfRyPZ(WNnf(nPAoZkr'
    '($UMT-!|utPahs}0>t;~ccf2%@R5@*xB_86s-gjduR3lF{9fk|3rxwlR*%%G+as5`e0@^IgI!1?QaIcIe}4q`;#|QDornL7FSy>u{ODeeGemLm'
    'B~JZy8m)%93UU|MZ@#N1F`uRn3J}3^BW0a=H%I4#E&>R%vGcInorh>3E`8KH=f-{q;7zSWchi2vTI<1RdE2}zn{Tka{4Bp`)A3*rur0SzHY#1R'
    'v2Dx=Wk-ZpPzdVaQ!8p>qTi9*XFffShV`53U5Gp7oJd+nT`^L-#i_0BmbESxB%^&&oT1)M+nJpa;w=W75$&&A=etV>^D`VE$g|EJn%dX&BIwjv'
    'nX&#{Q=S3Ww&?*Fg{1MPEkP$3k>zNOk0NV&h~>ZL&_;*DZ*?Q5uRbabL1Oa3h;<*(2sl_^vVGrGD_zm+imLXr32tWyOvGm7{aUD)0XxpaUbM-e'
    'Na=yb0_J_xfSQ~Mq5a>Rx8RSx!7IZT_Y8?Emt}~JY>)Baa#LEsbJ8$XsosN3Zu%VKHn^T$a&m|z$2%bmWpMe}y$x?99ed$ceYR;#WuJrKmsH2v'
    'A*>)mKY{S#IDE`{yvY3RTbxBs()9pq+FnmLdb1DSZxgxk5QdlZF$ZF+e)`UN^YC&S<N>H?XY{yrghFw~aZh}prNlP(y=cG?YqJl{nIh4b=45jj'
    'R!{G_4nrGYv~TqSTQQ7&CFjRIRK}64ub=(My4Q@k#z(<btrG3q1FQ4h65*<v<TjaDvkVFJO{RD$3bS)Rggxb~nK0W<j@8e8d;SZ8s1U#-<%%oA'
    '&D+c}(5a(vTi>Rm_?y@M=AS<g`-33DFVY>3+WPt^?lbYvK-;{<PKP(7G&^RZZpX^8P`RC0O}3W~X+5MB__3y9dv>3oSEhQOS1~x6J-e^4km|Fe'
    'fKSZZU2or$c-jSaqqCII!wOd;WTY|AnwP-p5bkE%h#L#2<i!RL9`&X%?8TQ;Xv)B*pWYeoJ;prnCk1;+d72@#AWqqgYM$KnQU5F({RkUXKf7DG'
    '>B{r+0We<FlVf_l|4bTT`*jj0XIi0d58`Ex3_@9~Mga*6tL;z0?x(LLre~Lg9=DX{SMfD#E#6GLelhJ4y?{DdC0TjbpxVD``^2?5l&-eDgFfFN'
    'K~D1TlycsrgjIf7+ij@J-P~2f2Fmcjg0Xpho^R$)LNrZ2YcHlSTmfF<l2Hy>)O-tyTsfXivYW_@omZ8|co?@+3%SodZGE(dZ0%PUrz5JhgY1D&'
    '{}I5ATp5>PwiC>|E-hwG%a6Lxrn76^Q&Dg_ukkX+j~XFw82PE)qn7>(3g|M;?~#1J?z+=f)tV)<5ZOnIJD)o3nTp)H$%rJ^nL+2<jlacfjUEjP'
    '?q5KD9(@BuTi}anCAU92T5*qeoO?%GTlJ5RS#v$+lVNShir69l?4=k{8t(9%<)P{mk{U3~IBxzm&$C1dBI+DlR+<liM=g6Te&e8VnmlP_{cw}d'
    'v1{E(eTP>bGliBTL1EK{R{tUH0_fu{%z5DLh1DP6@mVAbLTezO2Y<e`52NspOTfm8P~Hha!?zblty-H33EumI&a~yqT=O?H7+RYwIn?@``1z&s'
    '7*r<__Qxm?I2-)w_jefi#ySN9;=8Ym*UrI^QoJV3ANBr-L9`DJ;GO+ya-I}hqZQ5M8(_RMt~EtQYqokd!5s@dHqSJ8?=Ez48Jt$av0e@kO~=}H'
    ';f=TM0FyblYapA6b{6#Q_Izzi`z&3N```qA)EfF>P=6yWP!ZJ_UcWM>`H-YVes96>q&9I+b(~+JnbOmqfckz{eGDZkjeW|5UGQMJt#<6|_jTZt'
    '5=$YBhyc>c0*ROd^s@v(dV9g_18WsG>UXPJ<cB8c9>$GEeZKu<AT%xT*7$w;^EqI8tO$I&<Ub|t4WN45_(dzW4pL!&HJ4KK6{;Ve1mgDb?_%n)'
    'A(2>P%2;dP?rMrZndjN!I$BHnQ@S0Dv2hT|JN#83{(iCXERub0M)tTxTM(bsOtRIyQPgI(Q1deiJ-+#=qV@#2J60d(E?6#IYy3N?n{vw8<M6UW'
    '&VQ;a-NE5qd63a}+Zu-|j_m%NEljOm^!w!1%S(799|WDZHiH6gauiC!8#YFY^NRq9YYHA-?ZJI#4D3j2deEB@N@^u6HV@C(IZDS)_EUi6b`5xd'
    'vbFXf%fsy}V`u14y0z~Edy$mj>jWBdNo_BE)eoMv#s*cu2k(fMkZWN@S~XAJe1$4qe@zQqsS%0~xl<o)6-;M~QV1AK`>P;y@?f-Iqzo#p++m|`'
    '0GB;H6DIG4qx5@bhedzbdUX}so4Hr90C*x*_hlf?i=%f|{j}FL=6ua*8R?yCb|=p_y@I!|RX)?{-R?})`SmeQUdANMDI)AngbzA>0#np0Pn&-I'
    'x7$9BC$eoHnPg@&8&n=GIz28oXQ~oJWj{OTziESrJ$Z;)RwSWQ`CT2B?YNNs4hh-qrZ^{ki`Qk^4AOKY2Y<qs<DR0D!*N&DnNaV-f8ZMHJ>##L'
    '^U-@lH6wmhORh1NV^)eGo)xTXa93$=kQxQvKK0pRI65rX(4k77a9e%p58A!5!%27s+w;j{dzWhY+!RkAF8MB5Xzvnbtjj?#J1^FITs|$mXnbl|'
    'e9wYO#L^cTwQuX`^><Gi^~4c+nlfDu=-S~$h{cK8PUi7d>7Y?C;5R37VLg_@{4quoIk(<hRA}Ap*`?-KyH|&6*(?4wng}SYz@#iTq<13ilM1z2'
    '>V0rZahuOPI~Ut+0O6knc%AwMK4S6lZd#>ptzQ`riq#1+XW419Jd_^z>=B=py<wkU+ZmIK>^*+Z?f5_*ou6Wi2hJcDuN5i#t;zF|Bu5{lc`r7)'
    'NgQZ@kbAki01*@j7RITXxhTMPm+;mjXZPjid8`A6FU`h-QN7!3^L886Lmd)3^J4m~hF4#vsWJ0lR;x?gVU?e_*%2x_rJG)@Ii@>}t7KdT)jBzV'
    '<tcfXAgdvR-$vlWY)^iF9>|T)6@26TQlniFASV{iy|sZS`svzY4;7*k1gilDn&${Bs=>C}6K>*}yO(mJ#w)X~xLjeXYbxjNo7ZhPo(#J`W3fB*'
    '$?`Ic9^NvjH8Sw`bBX$zqK7+rRQ)~(@Nw2|%e`4SOIc3cN+d0^9sE8f<!sG0YW{YKb;H!jqH^`nupe)3I;fY;a`Q2fcPW==fr4btcN%qW?s}6@'
    '*H2vWyw{mpd$&t$-Q<CLy+#?+xg7*<G@bqCVzb|U23J`ck5p*>M1S2mewTpgz3!7sil~lUM_yVJd<evw2?UAy?oxdEgCq`?T#h)zDy}2Suu(k>'
    'Ydw<HMd$m~(7-69_ICIYbQy&Cv^(dYB@<VNqgabOB_3_5X-D;8_u9X^g)9##$KA)R_T@X)<>Nc1x`O&$Qi^=IPw`+es$z%rklwwrBxxXqvKn~g'
    'j@cGVOEX8*8-9`JW^n>$!(!Nfy~lCb0qRdKlLPFI?98>oPmHZm4XS(O#kic>J+0MpbrEMVY7U}-l1#Y5P;Xtx96wtd+~=^4#tmp6#xE1LHoXr@'
    'Rubg(!!ZV4yK0u(sX?f93v;&If$UyfrdC@)*LO29Ymp5wEFgWWbeS2oZ(Tk0Orev^#rAqAEnl^LuE3q*X+%lABkWU&g}wsb?%$oCoyBvEQaChg'
    'wZ}F2>TPB(n(^r6PR-^<KRU9yzXOBnUx@%zC<Sp(Cb0;T;~TBo=X2}0Z48Hnyu#0(^0O;*GU&X8?ecuzSMErLqiB{U9D<qey0@;1`-cin|J=UV'
    '#_PRZ2=kW8pl&C8Nk}jpJw`CS$>dwNZY0NbRy*DZ<GTZCcN`_#qFxyi(f<7+1qXYq;I`bjuFkF*E{5XJK6o#)op0F7>SNo|;${Px_+{=@S!$jC'
    '&O-=ZZ<^R|pYp*jr`cVCwd(S=eZLMz`<-NppWC}W`s{>|t(^q`h7SYahn;rqcP152?dI=$i)S*mS1!f|;$%LAV9ylmCf;p7dusi{87LtL15-KX'
    'R#;8Hu1PK-cZdE3ERn4a4SX{4uHwSujH(wD?0K*#3K-OvRcCaYtd|5qiRRR5L?e7=MHjBSoq5qyZ+}mZytu{zH`LM?8>CLR*t~uAI*tz-7>z1O'
    'i=;z(9;8yet+#_gZQ|uHQxhUA*OtK3e>v+@w~y9L^fX+sV@4HbEA%v3?fczkDda;o6ZZsjY(h_I|G8wHLFdR<PU|);t#L8Zbo2wRPlk(e`^_z='
    '*P(^#M@81p_(_9O&B0q%pme?550-hHzIRP%;!Tgr^1M1k`kxk@<c4^<U$#qcvI{CeoQ2tPHV1uqUhzcHzl1dgp1rkhQJ2-m`g%S#W-aZIA%#yk'
    'zd%?lCK3LTY*JCG__Kj&V(EVl(t7)*x>fmBoj}dJ3tv}1F_cBQ9wqqZhEajINr}t2^#qJxot%5#98%>5Q~zULUM}Wa_jmi`(eAmCwz7CT`1cmo'
    '1zyB#{TrNGh|SU~KEJPDLP%ELeco_{`>`4S9@S1~=QaD@-?l303a6rOYw$<ktH<C6FZWnpIbXL_dR^3kZqH3yGlA@WosM(7GC>7KuHE~-(^-n`'
    '@5A}L$NfRtdOI}&c3whV$+C3p#{0HxJmf|<q{}||BWDkn9(9mdzh(a9_C0rnW81urMWNyF-k^5#E{TnwuxaXZn*K`c@G9Kqj89RASI|tKhIYO#'
    '^f1O3(Fg`xdoHNBH|EGvmqGikK8BsO@C%={K_f55ht4#Y9x}fkE&vRPirWxaoa-r@+mp6eA5zpi2*PN-#Gf-kT0$sh6AV-QMrpGvfmb)dekL}q'
    'O_uC=If<KtoZS`blj^=tKOQbxOTH*Ic+e^CwQ*_eY3A?~r&^o!4_B~-c=`8;*Y<IUv0-;}Sj?HB2J{cVKxfBkJ}5&rL`KRUR4lE};c(t~@7>m`'
    'YkZi+C{-r5*(?^F>uNNs&wxd|5V6M#n1jzoGB%Y;_vnBn(ch-(M7v!a9mJY=c=Kwn1IL8vxO|%v;gpW`^Zn(o-19TU60SHcXt%PRHE2Tcg}=zz'
    '7p?EryiWHQdmKz2+#nWzXI*WLyt98B4;q^-QAr+8V5f}nOp_|t8}U#ys1Kcy9v$K6Wp*yuV;edL8{ecqSczOFz+S3O0=+rW`4@yNDle%(Iqh9{'
    '@&puwGoI;{<?qsv#|E&g9W>SCtK&ZypsJzTQs89MJU>_KX?*B1l@>6vOoR0rhtF*)41<={I3FOPJ(=G}%sQ&(LfS{uh}arE;0Ij<IHg<fW1egf'
    'gNC2m4)w4NApjR&zOFCt9pZbLV0Gg1K3fv4SuaX4ffaE8CxMVrWWN0Llu*5N7kqU(4X4fiE`u*xxs(U->~vbMAY?|$ou#&s<F_5P77&edA%*Ge'
    'fx|xXJvLkGrTdOAZ!}1HAv5r+D4`5h7Xp4Ows^gwZWoQq*5U!e`{NZIlE^;Ub@#RYX!2|cwF@HQbpCFQ7a8LkR@xoz>LarwD0d{(*4*kj*}L1C'
    '-oxGbZSnPs2SA@d9qb9HI(}E0RqDRDKeb?<Zz~6w-3tRSwZI$16<_n<vEK%<uDXLJ+#>BqwG9@{%A1y8yjT61`jq_0$K3UmNrR}X+i~;SwqfW3'
    '+zI%*yQ--_tMzR@nr<iAig83{FVRbO*>rSRKo-BH_pU$1cw88LoeGXH0D3pyTX!OcfhX!<w%~aN>9XwG=uVQ~dVG&s+S+W8M0dTGLNEvgz*g;v'
    '&xWsj8em|(O0~{ZxnxdHsdEsDGcg(wYMOS$&$P)mTfa$A3#i}y`G?1g`pX~=bHDAgb$N8pY_9v5hsRygQahK*=pc62-lH{GN{;|AkKNrMt%mdE'
    '+HOC&gHk;a4-)Dozm2ro2BVV8PxZJB?fpG5==u_J?9=R=8{g<fC8%VB?s}V5_3IU>mih~}&w;(ThV<A1CAX|BF7GkSfO4Df&|8vVr^?z4n_z-3'
    'U-9<vtT4xIi?usYV|lRw^pwtF=0rQ+p+l~9{5W{%&s7hr;#qQ@yoa^E1<K-D+l}Jnrx#vbl!lvfZa11iBSP^Ktkve>ezRoPY+jh8TW5pu<-}*%'
    'o-zCS4|w&<_ftlDduPtvU$I~o=`bR`GwX0pTP}4;K6bz0`I@$y`)7+qKaC9M0d<StAB{$JTp&Wy&!2V8GvuX-c3La$FBPN;e%R=?_pHPE%O(rb'
    '`qEhM=?uhY|9FJL;ReZTd9Dh(<ispJVDjqXq5Qabm`xXgIq<^HQt<iSMi8Ir3_I1#6mR-jfcjZq{_C9sC6i4b6yHByVf}Dz`Ec8!4zklUm-#-0'
    'zDz}{O+C9z>qB0mb2`s?%#(YgC&`}PwS1&5v3YvPNJfh*JK|Ko-MOpY-RtMe>vBP&(umQ1_orx)>2THeTCcXKbTb}5y+VC=f8KSWIC`3{)!G`L'
    'LuJSDnPEEXwZQeje$1@d=$mupv;#x>&v~5jBX7^^yOWpBufhiZJNLcAKqM`qiIDJdKKL5y2ZX_}*sVd<wflzwzqT{EKiEa{+VfV>@A~_Pyqktl'
    '-CRoWaAXArdwkfv1~1^J0e%LL<LU-Hr_9k;mI^Rf(bZ-et?=1n;)RWDN<T4Iya5fPw*^wicA8bSf1I=|wQEB!+c8`Hkmi`<QGZy7oh%i9SG*Bw'
    'Sc;=%zFJ>7y}BuO_WHVgiLs#2;%s>On}MNFw8-73W;O`!INJ?PP2{YCr(fF9xbckGJ15dTe$XlX9d5Vn=Jnq7f9dceb_YmM;WX-m-=Bk|UGW_A'
    'DZb*=&nt)9%gvVU)8OP0_WBmM8^?r@>$7%LpNGb5f4`=sB(losJ567z(Q;^K(Ba0H)N8RyK0M((55g0(2zFS%;<SP5uo-mi>*<^fr#_|cN4j-1'
    '25+?jNuEf&-cF&cwu9)>G|^vFxopVQ(=U;CIijvu7gHRXB;>*TG5?PE^&iMsQ@-W@d^Xv(a{MriPj!q*wi|e6U;8g2E*@3lul$-9`h1bdAG+Lo'
    ';bd{RqwWdK%iZ5!od)`7bNZ92*h$Yo#11oDL*#%Qm-WX_CGH3M{J3m?MF;BshDR((#HtCSi$%Pt0tNbOC6Botw<IC5&Wq-AF`XW+ed378P@MiD'
    'S{dic-E9b~s$u42f&NX&)7g?!rH!@QlmZ;AUcHBJRU;@#zl|9ye1!l`OKtXs#9>wcSld=wGv<R5zY%}cQu8PM0#UZO1+6AUwX-^0VUr2MnW0F&'
    '&$f+345i#!+2M+S$U1x1@29PflnL(NosSAbixvicH>4ruL~V$Yp9NQG3MpZ$-=})+pzppTcN23@DAUQ6B>x;W=m5!egg`xQ3q$atsC@n1xL!wB'
    '+IBTMB66;m@YKIfoo%H(;49V})3?rQpXvQu|9!YViKTK=%e%dtaRj*iaD{j$^2)l9|2$u<cFtG$B><{bc|07I@8fL^lO{ulI4@$M+*Yg8NlS=y'
    'tB}&aw(DCjhWA=|gG1bC@PJ3wC%HkN-NODW?J70L!v3|a+;^ka&{Sw-RAv88{2wE2f6DG1Z`Bj@8vy6@7`Krj-Nl<gM>z6VV3Tm~Kfg1qo3k0k'
    'Tsb(WA_*JsbocB@0<P4;_avMEOhqu7P@2-!iPo^L`w?7+UM6*J$&l*a{-Bc^Y)Nu{^I!MTF<7?E!e)wvW3F^)UmqR4)>k&l-vQG4er35F(`h}n'
    'VEqr4>R2sqNC^7mxe8IETmkCC%bcBDsm_5xPcIT&a$P@k9+ozf@s+S)zT3%Mom^Vpts-wFw-%8ytIuR<Y^`HvHunnjuDGQ4zJ%zMoDlx%Kx9&V'
    'ocH1)+pL~UufwM9h`YVOxf;Yz;dJ@2qKH6<?O?}POQDgq>&lJZte+z<xznSKc|OVBz_4<om60_!NW8Y&?-L6+Yk$&xMq3f+R$X#twwRX+y>zp-'
    'jHtulm1!+S2W3G$vZw0{8yhiQd)c!QiDmF?FI(xMt(W7=3^E+*AwoKYRc}ZNz0hrO-A*5?D;+n3;qFlYOtWYZtG9hd@6fW59quBhpw2A~z*2#z'
    'lb)Z#@TT8r?J#>O?`*hZ@k_}~uC<Bym-lA&+ZX4cy>s`!0n&0I-dwn+_XNK@y<nj{$LHAbT=(qUkLq%@fQvfO<9ea3X{oFxtpQosHKu{?BCp}('
    '%X&zqua*iFpF<J9WaV1jG&Z5qjMmo<H%wQbR<anBaCMw3)9lRyym;Ao$Sx<Y2lqOYYMm0mF8%JKI+@jX=Bvr3=9Bt&&o>w6+10zd`RN+}hdt!^'
    'DfZ>u&hmrzJmmpx=l1{J|E(+p{^_HW#Y?7sLwlG<GB5Nx+sYtbPuSyBoiu-7z329Xl@|?ufg5u|%t1Y+(tioGstpg9Q9<P+DfMEZemb98l}2|s'
    'rTd*zyJpM=BcJG&895k4<z0PS)oblq)<T_fNKV<mKI3Qeg*V``=Dj<!V=;3430>XLz}o##_w(9@x-+X=&Fqn9j*Szmsbq{a#%R%e7{smYbw}7j'
    'zE5ju6`Vz4vp#BkC#N&B<W^N=;y74V@7bE1A?v({ErsfBJ}K~y9Y|nsyH>jG#zg3O$^QL%+V|}Pcp3HnwLTrufjGKsEd7WI!D;bBV&gO(&!=Fo'
    '(x~6`Vz*Kg?r`XGBnRkF6@Y<ijl443igKhO-|~84$OAsdPV}??H%_e+2NSfG%QZ+J>_stx%#B9*;f+F48~}*UJc3G8Qn>!*RGB4{7^c>Z>EYCA'
    'e1FnB8a-#uu&ocHI-%a^$Xl&sQ{XrC0crG(#B$Yn&5VT+9^$Q&`w5VciT0X3I>BeV<6BUY9{WYbB-pMKDU>3kMHO4NspTmAbY=8<EF*Vz^lnE#'
    'b=Q_RyyF|TzhaN{sMRIKW69ihS5a7rO1B|x?l8E-$xAtt2f;&@)cJH2*0PQ_IrYO=pIWq0R#wq5R$EcCbGWR&MjZxWB#6}(h+<tv)BbM+zvFP1'
    'P@mzsrcSXZF_c#aUkb5*?<V6aPo~Ds?IwkAGw*A5TbFvPo6{~7y7j`DF7-{yGia|j961nwz*~lqAijK711jAuL|3`8>teO`2aMC|^rpM#Z8odK'
    '_<b<OXB0||lzZ(kz2<X%BM)HMW7o5=9krHQzM{j5KT}Efuk3U5r<_!)RVibxQ4DWCYWA2$<F+R$L<e5~NMs2cQOu`UF9X6I9=0kX*2FU4YU1e*'
    'J@v+43t74?>@4s(O&YcPc53Yg^YdzUlv%ib^LO6#;hnAedgbst`>(S{mseOH*a70PmGyZ6YzUTS$K!4gqg&%Lji=u(vKiA7rl}!c*>6w97{!|A'
    '{G0->2aUhz88*-js<&Jfx2V;)c9Vuub?b{qbpKn}gSOw;{O!<_TSq(ojGb$}jD_=F{@|0P{aTC?sx}VHgRU9zrxIVT1QSKZ@3t6-sxlq?K5B^k'
    'e!XimklW%=>X_%-H+tHuq$&Y*hUb!v(r`ETE13p2*W@;kFym1ga0c&HFQlACt}0KhPPPf@*}yDjC2$&$w0qU4Gh09vB^_m)5LFbieOdf_%Aejh'
    'K3hlE+v0*;Mn}$C7d!fT?mi;H#qhNrdfTpijjF93UbGw}y1+zvdf$inRavzCb|_xCbD15npKyNX!Wr*mGmNu!*qz=%d!LYTl}eBD=(wKhr?j~4'
    '=i0i+{_OZT-8P5%vsoby;i+q*fp%66b%Pjf+a1Mm9_*L<b7i`VCR->O!Nz=^vo82CH{Bzwvg3;2;p=ZAHVPm9fZ&V9ATzo%$mCQYwbAEn9kH7V'
    '>yzajZL}clH4NRY)~F@j6H;sV!H3bPTs5|1XIH(O=0%;g?UQT3&a){UZ^_?}v|f&SSZ=)Mr=~(obuieU*;#+t+U;k}j?<gkpY5F9)Jv&~-NpHk'
    '9M9(%;fLST-mqDRCft|0l&N%f#|2`lt@!xQDyV0=+a7nl%lyrE#OB8@@U9+|<*SGIx53nf*zYL+Q}1(*;zZ7F?P&aYSwFhT?i>%_$9vU$vT1rc'
    ';ma+9^}9If<07S_LQQWsd*Zu1izDN6=Qc;?H31bhgzBn?x8Lw`^_9-nXz}T9aKbrGE8Npu)+EcHtf|^A@~f+SfedSPWTo8nW!LFrP<Q#6IR7Q<'
    '+?v+|*D(B9jF{4xDN;<NQ1*%<I*_&~iS|-`_VxQ8tu?bc>ZF*L=f1DYP)kRLFuR{0>-w^aNV0n*VZI~1Og*({y+ekarILig8XUWMrFZTEiuF1X'
    '!^;C@*lSe#99tZuH@#1Wko4H@h|8%ioUgUP3kT-a_cL~#4L74xl}2Bi@X<{Bulni_kIPzDCW4hTVe%TBbK}M^J@4rr6}aUUFR_L=s<s2lM(XA4'
    'KIcnswK2-e6#P|7(SA^YKB`;G#*WZ8i+Jn;KW6&WY-rrA9B#O>yb;cZs(<bZ&i4-sD$MBm`$3M<K6z2o`VghM+~2?!b57UZ(o1ryG^Tc7V)fPE'
    '8=#X9)VVQib|DczN8;kbxjY|M@ShANtP)-O*48U6>;3r|Hm-u)5xc909=m{G<@eU*%{Slg@bQh;uYNxfAu~xvMYIPWu3t)5fssH1Kz8@yHCjyd'
    '@^<p)y$5&jukunk?%U%#2=C+#D|O?t#4o==cod2a^J-3C3+<bY)EF)Hyn&ai&EQ*UXuLb<OMsW{n<RH$Nj7oAmXY)X<Tx7T#O?2#d-oMy+UMq!'
    'zt8WeLB+9&|NGNe>o%Ur4Ji^jwW*I70N|~<eqC>tr$6{LYX)+)+0^-pUZm%U?-pWh9`Q~gpo+bpNr0)8G3R!U&x*mf8-~r0@{X>u$OlbP=5sa<'
    '!<m*j_kPi?Ho;!39Oxrz=x5$;p85~kQ}wu#k6d7(0ZBh<9JPtG*o@IC*y?@+2onAPY`ikM+Mv7=55o6O_igpPF<mX{ea-dZN*;(qlM(`H?W@2x'
    '@E>gF*vES$=A_eC7+JNZ|Aia@U4Ts3_1<)6n~L#uI6l_&^Kt2;i%T8vIm)n6ib^aHHMoCV8Ttt6PL}mqVjt<+>(JxJ^n3fzX4-*j)yn``Rji-j'
    'oNeejLfRLl+zx=&9^0jz);QXwwu3K5N~@L{GuuZN9n+UR6#AOZqO`&%y#w20jmR6@owmQU1gQrrr3PyDDMHG}EK6RQv*4uYkJ@%x$`3ESZ}*ed'
    '2S_>Z%yoR`_TE?RC{{n8rNN!+T0MSPv$_7<;?@-o8^*Fl=#Y5V=DHo-s#6M$^4C}^@#0l!;C`~JV<x*e!C&|pZ`K8hDe;?fjPY8YH<#7eqgS8M'
    ')9v2xeScGMByxfv>jU~?ATiSPk5l%q-IVY~-bcG=*gO=ir$3GM<(7Y=MOwm{31)5!VL9vvuiYQRb%h&$NUuFV8p!v<gw$YbaIi0@Ur}(!B|ooH'
    '%<0h;3CgbvMY29aD^_TuyUhzECJiTLJn8zWmqi^Gefs8l>*F-jCRG;_k7xc6>MV0IsCpHHHrDD5Eoxolx0Y;Ju*TRfK=F}$>@y9~eVE0GWO#nm'
    'YWI8E@EG^RrWzBL!am9!^ukPqoxl})a&o)N>gFB3_)vaVo!#nHZ8iN}tv3%sap<3J;;wbBF`VV__r)V7VX|3&w7ciDMh+_ogDAfmE*)Dei)^Ug'
    '!_k5bPi8f7^e(&55V{$5I2reDV7EWrEev#ESIOeX%eo06%2Uwq(UF+b^;KOQYVY2+XF1s}aW%sl^V%J6K48%}fGzVA^4{a|vbXx-w!y1bW2f@K'
    'RJikKHvI*4qNYNu>_pAyzVVyIsC)Va)b$B3M2*$|6mjDH5r5_KRq(&T46n7uy!rqSim+Qa*tnSzQZ8L5JD&B2$l(_mL@Mm}qgnruQL75=Q15aL'
    '`r<EiF49$8FLQd{&~OSoROE1YJ80y-%uJ*Yiv6kl1zLGoWwCI_9i(}$Xp+2S`4rXPud$%fb_JTl#q7E`CL@a&9e724Ka&R|NRcU{>0g|5a|ylF'
    'pWRIo@0&aEB4hRl#V%_=C$aBp7hP<tTQT9gR*KBFEhKh()pn6D?Pk)<BiuUcf0Vgj!J=oNMe^;f?Th(S)f2Mb-VMU<AN>Lksl3b)KE<haB8Gwc'
    '?fjM7zo&z~7&iYUU9a<3<Q18m4N1f0M?iAh9e0fre`~?Qb7C#&*CjiSTfNuDw4)W_`%t1nGzPDla_21#u6?(|u{AI-srI6sKjLKBfPQK`QER5b'
    '%q}W+*W?Jd!9}xMxLhubYy5IWec%}7*dk2M2f(k_34>|e{2;O^jFS8etz+j~0IK02ub}jzhFC<|YwY*44~YT5VvF3=d+?9@k;1j6z#*u$=x%Tb'
    '2`>3FWVBp_V0cfT%;bfN^Z@CjuO^uGt_#nc$Vq+RZqZ7Mu4D)LhjxHEJ@dJRSMh5u-YHx1)^4(Z+QB6f0JG|#7l+mp?tR)AL&ef!_&C>JY-#5A'
    '_8#qI;%C-EsS|m+lAi<47WY5mhpfgvP*}bZ%l8WK*<u~1@5R4E$i#T%z&F<EP#EI-#^Tz=LA@6{Zt<PZ>ag4(4%@t=&cp}z$i?dNhz?Vz-#j$-'
    'hs8w*-VTt`<tTd$io&SM{ldfK)=#y=%t-FLGv~WjBk64RcYkRP^1pL!ft(h<%(&01(;k=U(3#5><Y6u!f3W;M-ne_%sgI9;Y+U<JH0)1AshyNP'
    '_k}eZqf0AWUN)lj@gB=J)6jrgoyEl=>h0L}+^E-TQ~^S9AC~;tVPnmgD<3sh$?1L2SNOq=s~Z%c-7pBNwpu#Z_0rusWxPQ1sa{(SBK_M)&-Dp$'
    'E=6!Wjn+8b{{9|hb`+`Z1#jPc!9M3`-{9TrF6TE=B)gjp?wMK3IL;MGS^Pe?bvF89)7{|gurMOr>_dA>G?w1S8DqiZUVk-+qnsb7yXGQCM-|Zk'
    'w~P!uF69#$@5{LL4h{zWSq+GL>tl>Ny(P_>OJ?;M2k@PPbNl`61jO|?tuZz0lAaf?C=K=-z)hA6zpKe^RUpkFTC1B;E`+R<IoD`gImYhhr$9aa'
    'cBAI_W!rlp&vAo&48|689-S`J<6y0r8o^&j(z0RB!T~-kU1~db?#aOtcmBSS@U}uduJ0Rjcy_X(v`|L<`#Pn{`%GnN!0*3Lu9Hvp2TeWY_ve1p'
    'tYOc`!Q)4@&MayEp3sc)+F5l*rA?6!(%Y-?D#zNA$)fX;S%^TVbn<$z=z%$33GRREa{f+3bjQwHx<os`=wQXC`fxe;cH_+#uOf(Q5br_OSw2j-'
    '_SLI~8^u?<`&!XeiKlSjMUU3o{z`sP7n<K3k6Z*(NE1CX6fC)xMMlrbVoN--d9gU+3JE@YxXJf=6q5Zir5Prtswy{pV2eYh&~@8dBXU@+Io%h{'
    'ijx7BRUu!C(IXS-?j5z$2bVoIzy|1jz!<&b>2%e5M(btu^;`(G4TVdDc)?mYeqj4Aa>?1xv4+>>X*<q}_BSKplS;V++ru8P&DNQpS=h)gq)>;d'
    '*FRz=R>}C1!-NN<so<Q7$n4*gVW7Il(r>l$)$8~tggfM+`W>uJ{Xk<tTl42&wjFQKHr#a_(QdWoqbzru?`Cb%0<+WQ_viIvMm{{{G>#a3YjB=P'
    'B5kg9rrGbJAp0Nda~aCp6N_d=aNx?lln*6!_U|@SfeQEDN_wg9WJo3qlu9Gonf+kk!v8w&>7m4#cQbw<VtWJ-OVfCqo0`^16zBYCX6F~yD@&#5'
    'Am8@KY`l+6bVN1P{$bb+)&8Q}xLUQ$=bG_Jy<UEO={38Yaa&(bi5&)xo1>Zq&I@s>tp1EZD2|aQB1ubRmUf0Td*;fm2B1MU&ZiyqfEZDKxSVUR'
    'TGGA^LW*6*9~N!Ezx4FkU_-{DeP5Y-_fCZfcR`J^2B%J#srOOO6AO!uSGxr!b?`&&AOs<P4YBupr3^~>d3^!r_g<KSZB7C0B0kqI=y**ft?H&p'
    'SEs5Q-nygAM6=n#J4^>^K(rg}<8zsx90avkY_GKa>I}R}!gg}h-3n7463@E6+v>#dTAOnROOvRrjYhnbpS-t}j+*}9ZNx2k8osI7T>#Y3M1?^B'
    'H1j~O%%e}NEz8wvZnj18c1&p%I|{0NKBp$rE51q#`~VCP65uS{bP*CI8mT+~ee;Wx*n@5Qu1p1E(tG7rcp%G-t<KwkUfq3}7UQ&x?ySN<I=Wsr'
    '=o{?zGIJ-bdEC(X^{Qji<KN-F%D4d(a*VuRExth~NiV5Gzv9a9g1;`97<!>V&A4W>OFZcUq^GNV`zhZ0Nhql2w<(R_XZy%+H*K;<8bMt>9`buH'
    '-sA)S*6p!ae65E|4Pkc6_4f3q;;d=5imU#+S{7YRm(MGHRgf5;Qe^eDaBqk-mtFG_@3qamy3DZt&*Xy^WdK}iRnNc-v4SYtAghDUBw10V`+U|2'
    'qAt=z$h6hz;~?uLqVuQwT%XL09e>@nrAv1zHl<2ct-e17v<#cZ?{->zc@B8?`E&TiKT2=-9ieY2n>WTQoew&vK_G<sWqR)Ij;!(+IE|c>JZWil'
    'yH!7_RcZ}(dK>Py+??N?;0>C0z|ZB6qn?wZ?Ki7ya2_=~HR4g0z>{bm&?bCoWBX&$SEd~Y7SxdH*Sj@)BEo5|oul+Tg#7O!tvz_VgSwqHgw~2('
    'm+HE(Y;_cFcE{o82Gv(|lakT#@Qp~*q%|6$?CQmJz{a$l>96$2jQav!?fcE-Q6#77rxnh<#}@#2mBO_c(a)3UiL{4<ClfQ{qB3A-t&`H(DCdEE'
    '(Nn}mU-TVpu~(_d4kDqOWmr{sFY2#3l7HKzJZ5YAM?Pi<=oi626<PtCJBL7E2X0Yt?RI@ljnb%&<8^Ovi!6AcxcaL4kkoZ@R`!Y17VatTkUr4;'
    '5YNA&Sa&Y>?rz4=JVg(cabRkb;b=`7XtN)mi~DNji*Zwy)!E!_;jbN~SSjQ5Tzq+OCSF5v-P-l4g!kya3SQK8YWp3ii#1%4{z8n4LJECSyN5A3'
    '6+-IVvkLgRJVB%FYNX~9VOQAF41VL_#^0hd;?kq0g_6OiR<ybuqZ3k&Ci{MF1(UG*Xxpx^KK&qf9UrX*^0)tbC_4_h6x?1H-nzI?TE9=bR(Ur1'
    '_;lU+`qJ)uY7!fxTY)B!x>B25fVH&V*;ZB_GOVN@mzN)n<1G+2X^k)|F<iV?PRy7$+Fl)1Fw}4mj!uM?!6W4qs>JF$^ygWhxp>Ft++K<RHe%?L'
    'oT7B??TvI#>>y6;4sVYNd8!7^lLhv#YjK(sJjJ%3Pk^vYVT(ZZ<kRX=0XUUM-_icNs?46_%apHTug9t_%o|Y@<1bd!9Oi_ggI(9!<n$8OJBy1I'
    '@k;DuZ!49y3vJkq=-uV@Q8u-jIvb_s&KU*}l>xxICdO@fiM}v&Qp^fhAnA=NUK=Kd@;m(uOtyh{{KkGAz;=s9j5kuhGHWax;og|KKqO8kaDi#!'
    '0LzWlUvgGS(o-KRdM8uu21Ui3v5>X5V>~1gecdbT1OD9;DN?5o?^{3DJIroz+PB`--JfJj>^&?s!u4L}8uzck6`Mpr^SoaiS+&8l3n?5<tX`$j'
    '<=3r~uXL4p-8RmN-Nc&v^AUFS<r7+J3QSZxu`MT`HJQprJ+l+ezPQ1;Kiw>F<FPzxE49jSAktrc1aLv`%+8j2`$$)vt3Ki$lwcHpcUJi*8ylW_'
    '?wJAInxq0TjJ)i!o8LNCYhxe3$Kk(euO3qq90oIB(|-I-t<Lp-*fd*Y$7nz0FPlMrz3)g`xvaKoEQL4ekX3VI*Pl6S)V<yco>YS&8qQlMBIcJj'
    '5Taa0@_S-eI>OrUwYu;G3uRCK2U9hFR#E@Rdti`RsG4nET5p=jlHW{NZN9urfT9GxY`@uRHCMIgOkv-J1BRy^@VoDemf{E0>Ru(meaC9tF3R^x'
    'wPI-v|Ki#YXuD%@h?5{}?e(RfU!5-q(%j~#OTOU*?DI%ZwqDyr&f@Iv)7gp@$<gm~`YWQzND<8SNIwvu^ASq_j2@28Qu`6tH9w5yEV#gntM`2;'
    'WQDfRw~Uky1!phIm`oP}G&wEp@#Cj(K|f-V7cQ#yU?Oa(yt4>cn5YG-BfW-)w>5!c9cjG5^$}0~_0U4BZ4Y~oPtUiOvt+s@cf41Bx3D9nonG{^'
    '_l=F&DIWqi#%8syMkvO)ZJKF91lI)yX<ErtT8;f;j4$iO9UfhWe_z(#&7LhRhhy3aNO}-K-2P7e1>D>s#^|oGzcl@QcU^Q*I3G#R?l=28%Qp(i'
    'aD$w_x}|Pg9IqubG<pcPdu>b9^+^+#d+ZimKyAfp)qi9!Ae*<~Ftj@vamq!iZDLJ!s+6mGES@eiF(6vdrf3vv`u%L4!9F*=PlOs<C;C14bimbi'
    '4-se+ye1KcQ_MF8nrWI{2B%OX>C|5|axY9Zc29l!XhPZ6?2d)R)x2}qm8{_1AYb=aNPDn=J4LQx;T%EEt(0`4alQKS4qxL1y(?j7aa_dnUAG4>'
    'W)OMJI@b?1KjH4U{PUSdZhh1kdrwqnYLU}r_m6L?ZYPM^P#<QVqoeBFm$hbrx<tBNdX3<|?be=X8(B`z8*qP##)E=vIty<pTIWi&y{^9QqhW-P'
    '_pM8K7ky2=gJT}~+twraTn96MUzyi}k2$-Ba>Hrd3Eu1bg|<4hc3~LZBblxY{I2#@%H$4`+zws~jCLxh$J)4E2E6oSL~=s*%qcVJWas5rL}0I>'
    '&ThY7)gMV~uFlT6`>VAZj=LAMNj!XMkR#z-qr-zXSG`!ucJHelayO3zihff%wV|*Dh2ZvAqA9ufJzy)^nGpQR^9&CHH|dW?Vrf+yU^ZRc`ndni'
    'j_Yu}yEe!TJX#o6K50#=9-bCS-<eQjlT2#I4buXXMCmq;SbyA@;f%VOlV#Z0fYi0}O)wdqBo6NpLA1QBmYZ_{B4^Hc(e$}Xk%Mc4?k!u%iR;w8'
    '?>RQ@q#RFiK%m3seV|r)wHVN`U8@R3I^@-|!LHc=h%vvPDQR>?e!FtXZ3APOvR*o)+`+9r?NzzQ72VeAedfqnMNOEANKB5&!8qjWqbdEDUK?@r'
    'dwJgj`ZrYT0lSH8n*&Mn#-60h$sfZZ=zQO|tF+lJ8IJLZEaALiaJg23t9B5R&RP^w`C}+yw_>oXu=grMxwbX4M?UBvWhMjeF)7ATJ*{UAp3|LH'
    '#l>Xp*&cM!MRU32R1`eaJj+*<P~3Nv%6qQvTU80yk?lLP=}l*R?h^rYG~D)`HW~%0PAhAv{uM5R`S7Mk1U%fS_SGA<rpFhjo`a|{(C{L8l*RU1'
    'AI5{~V4-LJ;1(3bxLwvJx%0W&qVP~B(~3|T72Z-t#aD&x1t)3v!hE>)rjEzQZ|S$r#>stcfHmQg-&qe7K#}Yv6Q(EF_0?9PA@|NAM3$YqwOT6>'
    'rs_OuV9@2*&4a31`$DIib${m<`Zt|&X`QJ9uWH<J>&``+Af^#9m=dT4J^>b9ejnxm!Qcym$eR){sxEzG0@g>h;gdxEDAuf<#t~{^lWC`FQkb^c'
    '?tUaVVb#cG4sB`7_1p#*Us|&R?e)NC`{%!5y<`dhP_A)Lb?a;7K^oiD&U<j%j8BRK`#!+qcoc3patd^3jQkyLU3!6zdz7G~M3bMLU*U<4w(rxg'
    '^X#6F#+sv@f%iCsQE$+%$*pvG*XWTz4J^evEl2xDJGS-e$x(hlbbjr&#KmrhHF-ZD%2!Jz+Tw!VF7cSfN2#b*A2U<lXPuj=)WfyaU^bVvnM3RJ'
    'IKT$)HE0da)}|6xc7$K0t6}`TS1xz@_3h<oc4C5Bd$$=??q^yhXWN63Z<}8V3v0(_WT~BHJN6$ATuw2e?)QzGv93xlX?+_=W8?y|OS$<VSF*7T'
    'd(dY>K<Eh0E?IIX$zEL@)$6@+O*#{c*Alv{9A3oAqR6J-*%|!wxSXlCrf;2BxoXZdmggpgN?D&DlM`eZh=Xkf7g#{s?Hgcpo5q_R(&ZnAuQ|Ma'
    'gSf8j1ZFm&eW9X5;i&r#<a75nx1v|jnW_7~)sH>7|JnPgv1QuT$7h_z7vqH!6?6e?L$~x(sV6Ll*KxDoPS$Jcz`BLyrjH)9s4Z8WESA>_#Mg(<'
    '8c^uBc8BuTwevHNabz&M59;;%;j?DbN)y#!9ryF;50v%ue!Hl}@~#wn3!NIy74rB3ua6lCcc|a@dKxXH77x{Bke^*kcKAzsI`E*_ak?|<OHmK|'
    'Y^l!>xkW%_33d}@$C(Ck_%#0FWwpcaSEO-y*QGvx%a-Vr0Jhz5@yPZXk*g38j0eHycc0&FU#fCMXdbuYPc4S8^ewLo1peK{<ypJnxtQGPru*$w'
    'PsasiZbwZHdw7jn<bm#~+W8ANNV$him!-u6&^`jQ{cb=GBkkrb8y>k)EF@w!{K?XD={ONAE`pfzwt;o+)!=^m{-E}08+CQ7*Zi>g=hm1u8GdZ9'
    'h<dryVKak;3o>V)qn_ibKS%*y&#5=x7ya+NhtW?_6~Heh&+Q3qSl3T;o+UqXl>+q(rEKZzamXSttGFidMhb4{CAhg+<NaG_XjZX(dc97zl<xc$'
    ')uNhlFEBLH_PEcjKJW-WZE<;bf7wbOIZQf}W>%Z7K=@(vIuCS~o!YW6*V_QM0u@}h>RNF@ZuhHE;X0-@+@l*HUVYuMyZ+13)+%1l^C_*a53A!1'
    'ytZcWk0kvc#-Wvz{)^p3;ib*PdcgoxMQ(@VuYTGw(Bpce+Ea^vgIX=|B>t~3qpct8r&~pG_ip3<QD0T}^!pC@3}^%AWucc{YH=41mO0JnwX}qo'
    '+Rh9cZA|s{dJAeez{wn;n>Ni0X?-ev=huqWTQz8?`O$<y+m;u0HAP3p92*=YVG{q`UGT#XIczr1r_(!wnrBvj{mvA)U;?9B?dE(s9TNBR`*p1I'
    '@6)I(@Fu<bN|*l4&QkKwe?$GjA=;|;lIT>Se0Ax3q>u2DC+~RP8x0zrwN1yw(=OeKx%Z%NIZ#N%`CZY}WKIo(V{$uWNej1L85t9nd}|;_v)}BV'
    'K4Vr|SMGL2AI6U=6t1KDt2*=B!P9#>?YmUJ3c|TY@*BB2_W1Ve=N2%t-cQNOuSxW_>dQEtr%gC_PRjMLK<h4z9F~MFbx+oH=vp(m%{4#UNNG%}'
    '?Y1Ixo&kboaGk(Me@s>Bhn*3Oj0OPBIE`EL&=wZ?u^mh=k;n_qX?%k3$lyDvF)Hl_wObMF!|1y#-XjpkE2=l#>kt%<g<XAqX$A?p+Ut}y0Ub8Q'
    'JlYLuyIh@$!z15LdSd!l6Ckr*Ef{@!VNVAuue+-g9+K>3B~6`)M(xq%_dcTXx_X})DFIrCd}#vry+0!9iPCQ(k&IgfcFy`TvaEk1{L^OdnOy$g'
    '?TK=l-EXUOJHFrk-u&-viD>Wse7rjZ^Y34s-D9`jVAv}=ADC|Qd2Ej{NpHN)!y}4eAvecX{zKOuRPu>NP~-UxB6|GX!Tn|RzIzI{^ImNmUhbE{'
    'vlmwT@ciMp#UYsY&G|ytA1G1(*}v)>?bzr2b@-mL&Ym0Y2G2TgtXWE8S7U=-HIx_dbWM3DsT2qb!)Uc6DZ1Whb!c(hlVzm}=1#V**RHP-+uLZ`'
    '<G%Q{uwOj7^yal1bU0T|_-N!Dub<#(rTK~IAD%B;Rh2Dhvw!L`<@oslTbL0LVdkjXJd_r956@gl-?Ae#&b|pVu@{^`&IQ2e`R`Q}bg_314CCXS'
    '@Xtc3FUIr%?;K8*nWI0q(z|OMQX*lRjr?}oCvducjPnyjgHLEALNsKyjSN)(Xp#1w+44o0+HR7a@?NDgojTJ5YaOE)l(yl;YY3m!^)~A~co1+t'
    'q(yP9-ldoo2g&eh@kGx@5WL-uN8?tqjH}|s8$W9vr=3`iZ9We6J#Wj#_py2nM));X%F9Y?N$q;z*%slR`(Q>5oy={d)q60xzwxUtmLu2C2~Hd-'
    'qj9$=Ou5<edIx%4PPxG#Aa3lF9JfBB?_OR&U+EA}zllv_8<rOyQ?T9Oy6(*Mtd<wRCjl(N;pG-@Oxn7$yWAU+tMNcWS5|_%4yZdiP#GWh30q4*'
    'ee_c9@$PbYWvFw5gQiDiZL8x*esv}+<v*EYexo6NdA*^Pi{7hxRSkgFiv_yrf|Mp8@w&BI78!_7qdan$Z?NQEqynrrZZ!3@L^m&YkS<a5@@6lc'
    'd?QbUyD%FLkB{wT?0b_FIe}^{Zftvry)$gm?Oa}qPT{>Pe@k~PSHMYpF!ety6*jfHR+6HEY;gY~cOS3icpG1Ae9~)FrpfZX-PXT@S_Yl&g8Yhm'
    'erij9Vv*StS*?S*IBvtCh<`sjFKp0`e^2*$KG?MVF%exSqc+<s7}C<UZTg(*KW)A1tAHWQCXM5mc9U3GzsHX)C&5fx#2!K-JtxG5jTZMmEyUK<'
    '(M0Yk>D%9lz4p536=}tzUmx>W_SgmN@C5OrJM^isGW7J$*W|{6tbFZAi^=w4bJ+sRbp9DzOT9udeL6KhpB1E-{qu5kwN930Q*9bIR+as5Kin{t'
    'fbJY=y@lc6!xlC)fR*#%WboR|WY2qbl&UYQP8GQ=qo|(al{12lck}}pgr{S(e(2@bv)+@r*NQgh*cDu8FF8rQyw!k)Mr1GHwYdL&3$iC}ire@1'
    'i5qyF$IeQb)>f+gg?bxOo!2RXBEH)b*23l}<JKB2>Gd-1zaT!mY0zSa-*d!8%b->HI2)^lqr_cYWk7m9ozZLLO?{OMk5*$Cz1$%C(yJ))cCdU9'
    'RQg0<w`+7BnR%sgn~mM+e&f9dpfb!E<FOx5&MAlmkHh*{>MxK>JZ((H<GsDx8l)`rd3bScL)}HUTk3!n;b|FO0m4VBJNGzP^2|9|L)&@Iv>+w~'
    '2z}Fi&}j?021U<5dLK{Gp}TnEw+D%bcf#$vv&(#b&`eexz)({Q`Uh7TMD9xffjRVOU4HFocjn(D(N+5E3CI%t<v`hf(+#-44~+OZbE59?g%0$?'
    'CH(8Li!xxXk=})8Q2MeecBMBv+{ZXZS1EmtJMa8>d6Yk_CemAAyM(~5dLJ^^75xgv#LrfGj_)Yha@WEVp|iMWR$@=lWY|bh{;0;`ty>MYTK{wU'
    '^Rg*{PEY%nXv)uxf31}H<9@0<&iJMCOd5z-^|;48$*k+a>=NV4pc!7CC#%PhgM~&nuaG%d<2w~*Hk(nd_MiQ69yxoyM{V4(;m_{t2|>aqvJK&O'
    'oA*jIR!#$2zb$WNVXAp(f^GfEjetoGgMYST9T25*g61%{FF+Twy#dmXC#Z-%iuq#VwGgu#C>3ehYE7$yRpoTNT;<;CCO%VTU4X|JU+%rMbtZA`'
    '2Rn|jD%96bcq3nr6Nl4o=~7LjYk!4#DKy`UM+IRU+hY4`r_4&;23Z3S_oZLEG_S2XFh0Gmo#%JDJEwyW<bzg;5_bPv3|2FAvicq?*+KVOl{ovp'
    'SL^*ZI*^;MSqb)^fhE%iWTrpMZ>=kj=S^zCxK>PNl{?U`z4K5tr@>3Dj7W_eb3SbUZA9%L$}B}y)8<#;mhZdmW_r2-P&&Sx+<fc~*3n6@v>IO?'
    '>70XqD1AIEwQYsjk~LnhBCPftFLvz*H-^MvY#*&UQ{kEet~A;=&*r_`ZF52AjJa!0tX9cof1nlgYjrbrwf?2z+5kb!$?W>~YI)RqD{UBb3!xWa'
    '_1*Q#Dts;z)BQ9#R00<J3(@~OLM8lYRh&Dw=#0if;$^=*$NZd5{_Onauf}waLgNlSYqRyIK6KXd`FUe*^~Q!V+iPP}AAY_wX|Y~sZu3&FoSR*<'
    'QGX${RlG&oByaAaCnc}E-5xs<2%I++SD1G?SNygTDn(uM7H0{kTzHYU5^ToTgqvI>$6nSqFTuxXK5$M9(=Ed_Ar10gH|B{zXaMlS{k1y<-}ftq'
    'wu3IKTxu}8Y6)*p$M2Hv(Y31cp=RSQZsO;SG6h<=XDs@<Q^M1+c(%fo4PTBFN<ZvMWA_0&(;Fl%#tS)DgceP1y0;SL;;sP1%0*swE-SmRsP}u?'
    'D}G}CyAr$rTMrADZCbSBv6regbgbd(+dF);RN7@O-T7>&W9D-5!OTXv!zI*Wi7X}=xZd=o8JpI60d`bcuAyx$<VP@Rv=LLNA@{u6qFV<mu$wn8'
    '%iYPn*Ck2tep(aWdj9BL;q!Vx$(PSku8rlHr?#$}w#8rSQX~np1gxnXZJ>h-Rk7}L=O+w5CmlYrUHtn8kcT?twO8Hwd4yM6*yMG>OyAya%TnS&'
    'cEwYX_7-QyPWsb`h2AKeTe_HD_Q>uI(@pS;mvN-sb>xyH1B${2tyzN`e*B*Zwc+?JuVG;SG}8K;GCF;(wsMNb?ez3^mXB11OSgB{wq08ZlC86M'
    '+}`H4e$NkiJ5bqEZ1DAD9|*x^W1U#$9l@gZz>zD^Xt(3l?%_6)p-4{_e??(U*|Y;2#zv~9j~J47Z#r}}zcCxO%4d3eYfGnf+<Y3By$Y?09R+Rj'
    '>tM|#4ulZ#BoNbOdFiR^=NR*VHh5iq)Uq1~wle^Fp?h}gKM6AXp~ICEUpYF+J`U5j`t9Zl@jA+nKUf(#J3ZHYW(3U%IqY|$uLTY2X|;A<PkYP5'
    '0(u+y3vcxHYoAzSw3apXRn-5$VE~Tze7eWjQM<Kg8`Hd=we=fnPs{UuTiwj}&l0WDuhlJCU=)(RzMCJ}IZ^lB1HD&n&%W4QT+;jN+m~M3)$0{B'
    'nkq$BWC`5wAolD0IiJ6r%?}wrI_jU3vw%DA=IpT6ke5J4S}%vXe`aMX2Gw*h%*j5Uhny*~m;IG9z`eV@wanihlY@X=*S}RZ#5=W-zbwj4JGpNb'
    '%JY+m-6{n-^;?lQ7unu2>HvpJMVqe<7+H%=S{HNM5{T89@V>{w3g)s&xy<IcIdale7(SU=Tu*Ak&L>7!g2ftk_wst2DwPKBCSl){d=+aED+7B?'
    'B+jucP{H?etQs_5@T{X&m8vcQ)Fjp{cYF%Ycx|qZ=k?LI!4@!h+`cPzPw%bIH}pn4|00aUuzm@enF%Aa!Y$XGuCe&{J6XQ<?m>WD3&!mHM8JER'
    '{c88dTSM@XQLpZrbE^D;+$S|xq3B~DZQwCq`E}+_hC9KLj>o*5+JGq94e=mA6>MF`O&P7MYmTq3ge0Uo*=L{Ix9OiS7{}MRTOW7wZhJn-VA>$5'
    '`(~%?7+CNw%09nWYrjM<dU*8ooo!o3M%|OJFUH(o4?O$GVc4{MyAPx-A$VlR)4qfrKZrOGAM=7p+I`fjO|_z&@Q*g}2SB5I|CL<7m}Y>8t{3Z='
    'X`4=)Y$ad)+<f%PTh)#2@o~9KmdK<645!7u`#36_x$%K=<iTG0%4XXi{0-+6djON?##+}a!;E<?#Qm<B1A*0PYV0P_(U(j9)NY%GKcHyV@(F;y'
    '0d<yi<NkQk!8{V)G)?&CB?a;%5wEV7clYpEg*G^h-Cu9Nv}3+IeHy`bk;B(bg!#PNYj0%n)n&2Mo;XDB@ql<Ui{ZvUj<V=^=t$-ft!`N!ZR+H4'
    'fTWedhm-L9HaO2CeLdOj%|D8q`~1~5UWR>%oxwYp&DHNI^~m)%qbnD-oW`eiwVaf}OEzj_ZGpPZR?u!ozq;F0cKNxxoqERLfQ&C{Me$$m<-FI+'
    '#u}d=uDi;J-%K=h2Hr?9dChEYaUX=YM@>Sj)pm9S#1I~k7wN2#9PMie*?gQ|?W!dljcY%OFkbA;c>@V+@RtQhw!hsom(jmR_N*JF$0Ha0My2sO'
    'M$m@;A?lXBlAC-IIF)*EINNviRop0U-@p3hE(s^!HSq>xIX%)_XNdu=^SxR|ye`yl=fxYw4z!U5(B>*uS)d&KU`6X)A46;m^{<NqT5v<^l>nRR'
    '@4Lmld)&`v0h54=vh4|IL701<dFv-SLDR-v|FvTtxinUfAGe&$+mPcH-4~vMuKUM^Q#06OA%F_q&*#vpi8ozdqg9stXjC#+*O#-hJhdXFM^YKH'
    '6!uf0e=OVGRUW6^(JUB@i(q;r2Ws3JCp(UN7T<i;ww+T{jR?E273^<+>oJt<7xy0idhWVT`o0w3bAQAwRG=8h&o18v^je$d?`%E2xka+LS#RYp'
    'i3XY!VV({lN(Lv}xZfwk`jJZB6}O?Cj<#~s6RBNbfU9Zhpd*N!j<t6OQ&oT5gkJ+eFAJQnY^_~hf1*!6UVWcGHGlT`VmlVQ6>&L-3~o$@&uu<b'
    '{us#4quupuw)YS+tOUMT5yNv$-fsG`?~dB?lsk<bY@Us_l}epst?dII-G1ZIW<LH1MqVSDT_xNh4{tuWIsYygS-Z{sa{YI;NGQ_PDc(#j=kT&R'
    'o#Hh7?-iq*bIQ%?v{{uGh_C7vzcK%4VvQ`d0?Nz9W*pc2D@T5sH>Mc@K;UY@ouB_K4iV4U@YL+DNmINn#Iyo;k64ht=XGeWjNX*y>*b|C+NC@H'
    'Rsj|j93O9wzlwHcRwz2dD^ollgwuZgig3MbzW%sNwVG(J+htMzBVlp{SP3#kvzqk$%dIZv<J;iVkviIWLE#6nzo<AM*jF0U00wI5<JqqI!$ZBo'
    'OI<Xe*s57^l=}mox{Xt#<;jckD|cmsxsBmE4@~Jzbz9ANYV^gYckbl6poK*HZ?RRI+`v4t7fU0TBznUdZwF5jyykO_t_A-Fgu?hy4n^118V5VN'
    '>iLuUuXk_%DzjA#g|F6b|Lq!VMy6L)>ciJI28QdT4zyf4NxUhtx*CnPQ74`87~X<Lyn6W2{l+I(UKuZ>&t8V<6Ft8dJg|(63J|v@zd>?Fk1<or'
    'K&La99ORz7V4i>yGu-+<IIQRLGwP%oJ#WPq{QMj|<lT8qZ|VDS)OqsqX9j*e$|$!((=4vZL+?dTz}SG%1Z*C;IW>+O@onC0II>-Ths@;p5*{jm'
    '$M2xhdi`#b{pJT%K?!DC{GF_!ukQYS@Lq^9@W$>+Iy;2Diglwf_s`Z`I?fW}Ox63(Zt=?8WPojl+trHS52xP)hOZPkVw5Jj#o9m}Vt~qJ(v-<>'
    '&r87UN!{7@@C;6^%Q!gp&-X;lg|iImp|GvamhFzJ$-^S_Atfi4A-vy~*G;R(+H-$T{!OFX+b6&~JwK__Hz--kDMz<nt)RQMs9&Zz(DOFu-F%vx'
    'lYd-HF4bXWZQf?X?M}rCEcPOxTk*3>H5Z(aaS>w$HHZS8E?K=-CLXftT+VVwdp^~=!061)NILIrU!E+cb?mp*Tsh>?owW?6W>>?^S;F%9;<oj`'
    'F4O$0e)=)scJ{HxiC8yEc9M7r^6`|1+Xs$#tR0`6wHF)UH~Slr7SZp9d$nTkm&4(f>}X$U&R~^WN3R@gMOPV&`^YH=_O{~iBn`)#m2iqZo7qI;'
    '=C-@k0A6zicdDC`ThFVmp{EyY*MXj3mHRtVa~$rDJVs;Rng~)?>5VP9H`vhI<F>V3nnT8Hq&%=ruq(qa-&zKWgt#k(ofFl~SygY%pFmbi28|PB'
    ')FSR3zwsI7VK`D(jOreUUaLn>eXp4~>_~sCmig;_0eqod<JD_x`*u;;Xvnh|6QifqQ#be%ZS@`a*Xg@&SbExK1)-dHj$Arcza-rXvZpR%N3hSM'
    'W!ikt^eCM6&h5ir%IvI1LaNuJCe03L-agz$c7ePle0z_k?~2UyCB1{Mq)!)V68^XOXAi-$P&z*lPsY1iHin;rclPYa-wv`dCs$xOr}%BX0)~q&'
    'k7p=y2xpEBYr{(G`smDTdOsweoer^c_>^(Z{~j6_pYZ6tdgCNXtePH9X334{<xN&=GC(3V_j`K$1RwNl4fLwvpylcNx<%Jxa{w3OstNQO+_<BE'
    'w<E-t9M}J8;@+bto;j_#(u_=mY+rLH?1rBXRG_nH8`S%UT=+?-=<^3xRYDO7VGI?3D;Yxdf@Y$YdFr?hT>A#2_Jo;>v{dU(PpdDyuU=J|{`TZY'
    'xS&@9<Jla~Yf=mSlm|Zr=i&M+i4u;-D!G4Peva*v*w#sLQB;nxEn;!&AZhPL>ntDanNE>x@gRxHmlT8y>`yPaQB%$*nSP`jaMtmudL3t8WDauS'
    'g$(JbA4`e#>^!bIGtTwAdFFuB>+FK9@L7oY?kYi`Hl|TZ8!|89%+8%p?a<|kO3#TgTZ?MTesd^amkhJd7U(clb-;Kit;w|Qegf777ByWUKE0=^'
    'z}0tY`CbC;cHbiZJ0X+WJz{0^&-a4o$z@va{a0k49WGYZ?xfs_Gjecyg$0ggklyxZXa5if9V38;EdM3t+hkrI&xgNt?)BhTcl~E9wZ$~sL&Ich'
    'zFQ0RI68^i*aYs)>x-PEqzl)z*24^)n~vO2j+VOPnyDN)4Ob0zUFkQN*K|beOztk0{X9B#UYVnWLcIz(Rn?v*n=5UTM6dR=4ZGSo_rkxz3DyUs'
    ';eEv+m;lS2Mt`%N-G%r)Dn)AQ&e5xIo{Re~;pkQIHMp*kr)6OZW*kR)v{|dKxblAf*~a&>rikuLcK~!fzY;gefvt}a(HORxT&CZt03$oXY}Ral'
    ';Ks2|e)HL+x%9|_1u5im0`|Yqn47KnL_7F+9ecUm6v%~fA~aC5M$5;+wqKhDPnqAohe(o77XE`f+Y=pom)VRj)MzwN^zG;eib!(f&L5Vr*Twah'
    'z}wSE!1=ep^=?h^?YSxWGj?V(xjm;J_+hq#&GX$k%1@{(to^k`EEVuQCF74lb~}AJZ4r-fwk<_*`BdTC9eWiH$=&DsU*O(ixJ;(A9*5Xyf4Ho{'
    '-3d@(QsxrQ#6|74^ublJWvyecpqlH}*ps&tA*aM?-<c|hJ^#}H^ggx5TJ!t<aE%wfsQ;>S+dFvPN1twuM=^<aG$vf|KlxjUAYi%6wRMcTP^I`y'
    '$dW_JIOhZQi+7d5bZ!hLE$a-eJI{UkYOH<s9@hs_Z?+*<cWZQ-uK}>q75n7sH*5nXTI}J|J-k9kqB23Oim*lO&K5Ru^^9GEThV6GS1rvZXLq)l'
    '>>7RdlJ=nJR?pSu`O6SdcXRCHA1k}8f7)pc_=?G1VWVZOYiG9B_^9%Sdp9p|JE*g(zIl%H?4>g$co33V_x8Y|K7)+<2dW1Z__en&ilf9+D2q|('
    'HSVyhXg=DFZ!_kjT>aW@e9UfCCXJSH{DLY{I7L1hBs(>}(JH?%@TTZ<y~Z#*^1iU=1agqJFPFQ#=jU#4F5@kQJ>Fb<6<DV;tBqPh@&}Zct^BMc'
    '-4qF5i}4Km14WEYA86y24VA5Y+an-B@RP3gUD&7VC4jfsb3Ygcv?XVXtyZt23IaHO)7y914mGZAhsA7q|EVqL#>@BDUGEW|PP5#jV<YG^9u7<K'
    'hSSsam~HmB^x51}#45QZmD~QYGZf>Ee|!9(wT8<1@j6p^<TOTA?|Zlz2WoOcC!HlkJ30%A!a7?!>&s3?hL0LRu?O;U8rN!Ucij*{P`aU32;C7u'
    ')(w+RDl*Xhv$j8Sd&mo`F$*1uz5}xZJpcJxqaEmtmZPS_QGegVD+n5kt@3$ZhW50jW62?k-i`IP8xI!u%Vd#u)LO<P;@!G=!vWUnmXsCKJ}2l$'
    'l&0s?nihS`CHB_skj-@y`^)@U(QdCV*D^E?#iWye8YlGgR>WY2g=f2NZ}-nvr)ydcDm>&^_QAZExx-5j*3YmhJg)Vvt1;KkC9YJ#^tLmKfGiix'
    '+RHaCdSs#>x*A`8Jdv#{<hyvf7V11QlyP>=V}H-bcVm!XHE2i-*|ll>cDjVE*sy4KRZ=O`!Bi*VZJdmu`?a|_8oxyFQW3vTfX(G&4C;#(vjmI5'
    'b}U;`h@c;)9eO3?jGs~YHM2IPU{OxZ2f~5&l&DjIJ+GeZY#WMS-l0n_%6Clu!Ub>)iV<q@t9Iv*eI|n6tUSI?<3D7b>+^b0yNCZ4gC-fX=^%|l'
    '6iSM8zzb2yp`?SPRDb*a{@y*$-fw!*Ofwei{@mBKXpxoqu?b4B2^3VoF44hD@cU{1QFrLuF`l$4i1k?==PPBnV$@%Cx{^m#{w74r4&B<Z3y>5+'
    ';oNcu)qk7Yuw`+3g?Cjl#idixp4aSZ+A+$dwVS2iktw;ZL^dfWW))JZ@ALXIk_5MRwlDFf|Bml>+#Z3>z+N?=pMTzxQ{ZaW)s9X!T9)^Bvb=|^'
    '<@q$9-ND5w9xT|#0bfX^{-D*`+eA#tsfwMkWn&?|`E7T=0&5&r&~rN#52I}oBRvAXKL?A(i<Un9J6lZ+HhDFWQ+Abjn**1~ZWh#@*lYf%)xMv+'
    '6UDHNbg(DG;9=#$VBCHV2FxF>9gfb6Y+_mRoR<>X5ow~E;MP4KjRua{oz%uoO>YgZnYNInJgA~SVodiur62)i<o_NnE8Hr^rY*!5aMzs25~Ov;'
    '+7F*X89W@knn90Dwm7>L!fQnX2jK-GE2xf#9qk2C^#CnL^jW$r;;9xYE#fn`!ru)|1FYWAOW^op!thXAr$TQT(w)xs!Td786r40A@s*yPl3sd-'
    'gmv<$h4*Few|IXqW4ZeL?!-6Ar-O9JgjE%r42;G01vTc*aB4w5U?0N0I`7nZUBA!GcXrpSjt)2a(QJM?Kh)AFo_yB*&h{2nyNiUgIrKvX>jDL*'
    'mLuW1NZ(eUzD#WS5tndT&4q9v+R?DxRQhtHp1w$<D&hB*SZw$4mm5`CskS<ojh=Lj=4{lDO+nU1^Y?n)0&A1%<yXo2eNl+ocMm%##*FdsOMb^G'
    '7vJ&f+7#;H`M!RhQ8I)j>a4J~B&?Ms9zNfT*IflpbMe5-PA8q}P`AqcVOPKij(Taen)l?qYo6TK_$W{7>#iZZZY<#W=U>o0_R9Bufzk9wUvHP@'
    'A40m*e&y&Y&eDy|A1mYxwXH_jR;ch^$$&!gMhWk)V|QlmA5I*zv{|#wTh)vx{hk?x^yhEjReiy9L*0Qn&0L&2e4U}IQF^U;r)TsLH_lMU-jB-7'
    'J5TOf8_s2y-Jw%7jM)$#QeG<^tqqK?EXmz@R?fPaxh9^0$me+EBf#m0hkMSU4*gl1_g^*XzUJ?(IcS`Z#c@`t4~mouFL-Njq6{Ymr_6Xa4xbTz'
    'uH+yN53f6D5<J8lf9VGH^(=oaU9QDgZ>%w~UB~pz1FJRspiFO;!j`j|i_w8+OJ$2g<pS?Imxko`$p_W>{nTN#{};hfyf{`%V6c1$m&qYJaA!=L'
    '?P@5Sw(2jnUymzQ$9Po@rF}>H*@4yQQ@U*V`~4spzNP&VE{p8M>|D9MYw@rSVKFo;UVqAn$$9<CIcWO)n{f%>UG9z_5QEzS-&|NkPvI_L7H|)C'
    'c$-W@5Noa(k328Ul^W_91?1HzU5!cYHfREuT-3Amm=85;El2E20!10N+Hv<GiW9Ea?)$ePT{L_x>7v@foh(2_4!L|kMFVb*fSWJ1<>u*UUuW-q'
    'Zv-62Y~yl;yymw|`r@N_c1Ui&YHe=#*1)E}^~~&IO&MwIt;6Zpd~`yk@hNgKs<86boHFBqK3g>u2&*J6T}AtocqDq+6CY*hFuY7ZJKh_N+1^IK'
    'tsMmW-~%>3FJ9_eT!h|Pxy?o&jk#j#L`*tsadkf_=r2JlcVwsN2?NTr%S{;&dYiwb_f{~XVnDbb{aYXv*JV?ZBnqvar#q9ZJLT}KU8>1=^*9}u'
    ')~AHWS~YI8fa<o)GfvU+<we*O_1^T)!}a1cITrrY%F5!hwrJ~JxvD%j3-RX;f=41aslo+pZg<q=Is9DV%~Tv`)=fH-gLk-`6nl8}B<oW&W_>;G'
    '_4)&ud~0MO9rE>47#5S4C@gndPy4Nz$WA6+wg?CDieAgN_qb2hhR^q)B9SS??ZzAXyQ*WC_9FP6D-&Rh{T<;fyW!IH`exYu30M=G6~7vi8=O4q'
    '*LZeR!ku4VLg=Gu8JnkFm9f=++E@|TYXvt~?{eVh_TH)37mn6PmKO|dZvdcqzvR$rdaO7BIe75%iMnXZLlp(z`C$fsMlQPv-FeX-c8Y;mx$n=U'
    'ozML0kn0sd2%eTNu|0r<_F}#P?rB}Dsdr;FuPdZo;OGLKSWQoiI?A6B-@S35O`Y>lI0FLw?0%Zqa;JVLoB}`V5fTlx=V(lsb@X-c=+U}9yC$92'
    'r-s6d^HUZFN4L1HT-cZh>U=^mZGT@mu0YHl-5>bNjR0a&bo&jT^|#eOJLMYb=?-yOLe|st^JfiOQXUyXHEXw8Yn~y`MuTyM_j&x-ndJnNk`sJ;'
    'Sml)sBCj!6Z>rA8^pnSOBN>6SbEee|Y_Bbx*xo^8{8ygGY$LXq@vRd~h-mAxJvQGlNW@^kU*Oo+cN8Rj0|BM#xOxUBZ2z`?%lQhK$JV#PKIZBx'
    'y{vezHCmz#AgDH)Tg-TiO`u8{>tVI&o=>Fc9PwbtSK;xHQ_^$&Vf==VQQeq|+bD2B<oVG09f}Hd?${#bt={1ICF&RYOL|>j_l6tj_%S?xWPh-q'
    ')!V|XcS92Fc|yj(^?D~i>HFc#yW6=|16=lem<lw$Q{koOf3NkcdO4x@dBbY1q-LuEf@$U0e@4!q&naaWv+Iw#8MR*6x69yWvs*&?fX|or5|N8a'
    'rF@X)drq(Il#Frp_HjjL<PQ0zVO^f$;4=xK7N#pbJNhQ6yVJG^cW_+wup#jBU5=Mmb~D8ulb9rD&C#9SDt}qvCYQsXE#B3o_j4Vh_m=PPtdGW%'
    '<Mm)q?7v^d&tkR9EmvDA?rhc%M2#(m?LJJC#C7m&H*>K29EuQnQ~H95`rR4UJ|K6w%XW4XQ#J{tK1s~ub#{yKMQ04j*Hh5{cJu=^Y-{8ofwbw;'
    'X;Hg2&OEi0UM(o)mX2GU&BDhKp$dQdtBb1;hf3w|9OGqkvu)h!Id2TyDm~EAG+VXM@@Hf51Z}3Zg*C<4$8eC<@>wkJ)SG5Sx@JyBr)*^kw^KfU'
    'L+SHb0r_kT>fJs93wGXFB>il0d|jkR;YxAua}x<Df~B%3Okye}(FKV{rW@Y4qiE77laQKuIn<)<<0MCMmA<$k*(abyO|7Fh3dr058dc-^x-P^N'
    '6Hkif7L?w3Y4VD7e_?9y-?t-%#pRUVqI2M>-rN7rhgWIl0q+la<hDBINoT+VC$N9YqF?{`t*q_xSVr{-E7d_rEPGHsf&Rp*6#gz&M6qsIG^XJ6'
    't=Tn<T>Je6cb<F+8eGnYD~iKkgenPl8dCtw+f^_w6r@R}=2IaX!})k(qx%V62^MRbuAz!Z^`t9$-Z#9&P^uN2?mv1}zb4;T_POD6+%{#JR0c-T'
    'A4of+(_}pLLgGyGt;!<W&CV%6r(UzzeVq#{zk1)|u`&m3c4d6XQ9F;vh?X{d7@J(IBYpl=>Gb#8@tt!|ZuZr$xS;I}zBcCdD`DiVZ2J|2;bpU^'
    '9OuiW%fy~HIfd-x#7<OfaK2K%f!n|;TyqqRw~^H9Y0X7%Jf%2Ki%M`LSEKeAeHp+>DGc#~WU+J=9sdGnCo8aV0E`>Pse$V~dvzDZ<aqrYO&odv'
    '*BbaMs8^(F!gWI&V7G&y7su`HtkNKLXyL8gtL4^48-099n!kB_O7df*+D0n7SLd7<dS_W*?@OcFh1bm{g&u^nK5yFn$LYFiLNZsQaPxv8=aV3-'
    '%Pq8lQ}VPg{L`e=kKW+f|7rxcJC>u>Shy$+o2WhqgciDENj&Wr(cUcp^#e~9p3xcAX(N_M{<fgHN+906K-eSFggf-wjXY17ps`)fdNGXbboHS('
    'UWZZLKK0p6Eok=_)Aj`%TM~fn9tiWhA9}J5T`Xd~pBk|TcO}zwdffYQIa%+1E2lQXpmN%);>dAN^0y$ixB0T=4Ytt9YK*GYk)PHcXtq4k-OAp}'
    'Mwfkl4)KY+mn-`Dpc&5|{kayR=MZSx0ls?Pp9yl$YlyrJQ_iB!fuDN};}83VY{o<_j?v}3Hdc+zvP$|}jG}l=GOLygV24p#S7&3hZ6<G*>K}c5'
    'QLeY2iLzIUhqL0A>nwuCiM-vwXG^Y(k4#p-p2TjcuN>ig6vwBeuTC|fA$)arE-xmQRsA_AY7ZXz>K2Nnv-5|u%}nUTFaL4E2JxXjlDLgpN|XdG'
    '9NUp8;!jwgaR$9>aO)r@ZI_Lh#_t`qbUyZ<xb+^m{G=$LXZJ5BtaEdNj+9>ZI?(LwUT>o-3|GZzRoLhIz^6v*A2!wGPTQO{gZ8_wrQ?-iHJ{xT'
    'KV}yqP{0_mU}I@<{S#g3y=u>DQYnP-U!SYl3HwU^`hYx+CIgbtJHzGHs8;Ih`5ny``RjAGDm9)M9K1*0#hH~Fyl#z(J6=Az!$nZhq5Ylj|215W'
    '7%wwnUt40y;l@u}hoOt;b6O3cT*r~~XaLR*+x)1cNefWNkxT?wwR|tYJuK+W+8sGBu?0`Qz(7RkVVkae=#MsJ4)ST7QY8Rb<Z+lK6@^A!_^C+~'
    'rA{;WLX&!DCNU4Q5#3jNYJJcL?TJHPYL_M*obIDJ?mHh2JivNI)+&RVtAP_#@t_sY%qKt2g;6j*z6VLdwjcX$j6AMSZOX2yTnoh#vGT1zm&vGP'
    'uYJ#28{NHUduMTRiSYfi`0Sg`azAyo_5xvw6<tF#e3p8j=i^G$H*B|tUIFZ0EP<)t5$+8__?<}3-bdhehn}W0Z-Dq_#eDd!BGy~^tc6{2WuaG&'
    '>=Q7w)=%(G=WrM3`}92Aqw`j~M+~^Tau*B8_^`jv)Y9xuUg?iCyMi|>9qZid``1@n;(h8XkNkE;^oyEtmu!Y#2(LxQG#g&q-Dl%;_Yqy5De<~9'
    'NSEUv`l<5GHNfmpP~n+S)Pk6lxQTl%Ar01=GPbYFE2U9K2xR2CQFl+9oRXsojnB=IKJN`G&HB;$j9Sg166U5Fjw?rEHrs`jp^dh0>d_R9^W7vH'
    '<?!C4rSD@g=CEzODs0N<G-U2#DD>LZ?rEM~a&AH&y(9g}v;BAGn0g08U(EzKjIt-)2%hvT9b*Xn8cQPxP=uGq+8|$%TnBL%W2b+CeQN@+A9&v_'
    ')A(gZv~;d-3V=&5dA;^a4n>sxxwiRXk?yQH2ej)8_Ak<Ef(rC&zJb6+oS&DcS?aXx#|7OB6ZvlhqsF<e%%zSR?SZ4Rld1w$!qK#uEgI-1_-&g2'
    'BA3yWY&z2i?)GmPvvOnPd8WdAJp+h2`8}HFCY8pGc^kUFvFN97*5ymm78g(wCN35z`()E$xGA+(LWLRUF70$7lkkdl5Wh!)+g!I=us(0yHt~CX'
    '33ifk&cg}u6J|QbuFj|Yeg$!LxHzI)o2p)xU4!M2<9UV^@(TL6lrw~0C|Om8V~C6H)jxS1Ip3wUjB4c*JFTwm#gsf|7I&)l{NHJ%9gm&UvzA9!'
    'G_G$i1;0jmGhg6y02x|jS6V)H?!2j~thUNW=IL-!v~33g03;LrN3(~e$?SWc`LChd3!oV%Y$^Tk5W`8GuVc;Q#3BaWg&LdQu*Z;jW&TFV-HaW1'
    'C~-gEwuZ=7&F+JOyHH)-`x1F74rQeufn9Hvd<cuyI>XTG{~A|vh06{8PjRD$I*<q3ZAY=xM%}orEq2ll5A)`EVeiI|$~|<GPv5%_iha<EhAvr?'
    '{BX7IzxVyt<4@sNBj8y~`P;91M1U`gpSEzuJQzhdxc;n84S@N|F!49H-jwQzy*<7CKvw7LT~l8tqWWn@+`>G5C&*p6v828Mfc>Mlt2NUXRRw$!'
    ')&S+f2a(+=aJjrso~XLckEn?z{d6<E5Bhf3B+R2KcMhYl$H-5}r@N2qfCMX+Vx@DgN)XA!vhQ8%Mbb{~Q;qv#Ys~&sp*iBw02{dB33Qmb$i0TE'
    '{z=2EPk8D=GPHwNzQRuG1CwwUKezD<C)M5Gh%5U@rS4jBXSR#Mx~~Zt%tgV5=)~8x${VpcWC8&eVz+kackX-a1~Wdhd8HeNl^cr`nK!SSwTT=r'
    'P*zm&9rM!e=&;_=GrsvmUk%>C;BMv4^sRUu^pLB6c;iQOeKQ^O5A3-aNutlSFd{nCkJB3Oj@&%@L&K@05pX4X^o^p$g{W77c`ojc!5F@dS7lwm'
    'nfJD{|IDJOXk>ararpCx3gk`y>A~t9`Vm99azzeTJNRYP%r7oW>()qBXWbZDl+{Jw!#|;1UwnT#K1fYCrzBbZZQ-c?mK$xlU9Q-*ZEr;;33k7A'
    '<@W1!&ZZVhWkneZPIq^sYSfcs!`86X1Q*gnVUW&|6^dDE>bI75<6>G7ScKYQWNUmFdUs>krz<e}v%&G1?KdB3LZ7dn4C^zmBHrdtbT8>>Ew8A<'
    '(C#$=oo}zH@Q1o*96T$HBHKdKk-<MFlUn1gU;aQj{;k#_UhBOFJ@~0UdPqrdLH-FB3$%>Hf?gzD-7~!q&#&EuG`+Pe-~*WsK6;&X7(j2oMY6Vj'
    'O;6rsxozUeZLSJ+zC}D!Y_~lUC1RD$xqBLi_u~Tg)664_)~k(saLwBSVAu*@^$GPJSN5CXHXLJ+I`0*PIe9nHc4B-Z^m;epT7zJ_CCLV@O*e9y'
    '5}5lQ8BA~YTfH{YE;c;4cPBeTblN)romQS(VAD=|`uVQS1^d07d^;cdxou8=?;vSaU)AdYPsjDnRBQK*zUHg+dPglQoL|gx2y$p>yk8I=f5+*d'
    'wNEVI7;s0^p-As3{;Uuu4j#Q5CnHX~4&q8Yz6l$1HwT^N`WPGlbxx<9uipfd@C1?eB4yMGGhHpQ39q5jiLNw*>gwC{Hm}-@RIatOud>e=lWuPc'
    'UI5u9y&USo8w1N~U0)GNUfaimC$a88RVit}$E^{7Z{Q9K>*~0TUSDs?sdX!h3t!};nz?IFTBGBMf%s%_Tdd%!_L{Qda1K@zvuO-$s|$+w%WPqe'
    'Ysk>}4=dT-AABtR<MWs{%253C$jj3|FL(M_1>!he*FmeI1dAa6|6X+U&D@p)FPyIR_;jto;irdq_T0$!A3kqw;MnY(i4T$kQwNPK#0?ha_?U)N'
    'axva%O>f^<?5Mijlfrm?*eZqB$6i#?A;EEt<x=K+&DrwngKZ_$mo%2`1R2rcY-M%I4L@^FEsm>b4&9pimt1Uw&j5cfx@8*<+MV64xfMI9Z%<(U'
    '5RJCzU4yh2zW*iW<QlwW&w+Wr`fPcV_{hG>!E5mTchf<B74B%&x32QYaK1luJCe)2e(SkVmw1v;WT)d@vGh$p2CAP3B-EExu8^w2Kx#*Pu1+Ts'
    'AeHfGx+i&9WZdr%^;+CHuI=Pwq0PT!u^1(6%I0GYeH&NyetZC_JY^o;^jrf}XW+IUB|II#A*jcFsk|{XwY?J?ubJRh>)8joWil^;{KB_Z?@P_i'
    '_ys@4itmM9Cx68!Wn;ay&EB}i*YBTKD@$XBYPHXk(p45RSslz&Nsr90&DQqRaeJuOZ<}lvC4%sfAFXD$-L@X9*EP;|-irFg;P5-`b|jtz5M}XA'
    '<z+e+S41y(hMN8u3Mgw3zc$v_RX?um)`@&EGbp@FHb>?eUR>$9!ysz4KSRmqw0Oy3Rno4{iQ1@aj?<El9u+<^#;tyJXd_IB#yvh?ip06&{ip>('
    'JF^}ciE!ii>x0^?4isjULh*bl(bn7etB2hVLBDlX-0QaSp5+QT4G_ntVn>6u{zO@<8kb>EsB5^kR7r~oXOw#DPL`v|BVy&h*wS~SbK{vJ<W8t@'
    '_Ec`NEet@OhPdRd3vNucid-Ftb9tQ|v$i_EPnUzIzvKJG@)`F|#D|%AyP$_Ds9)?+s;2P9-4z@2vzPj>k_0VWyBAMP16AkDs(%Xm-lzaJMPKDk'
    '%&ABBGg&Bl(^*yS269*hy>7KFOoLxTy%^tb-Alu;h56i3Sm#3Hk<8}`P?razqbRNi(txh`Tk(XXCR3t&GPy2o!V(|dLbaIcvAsH_v-;h{jEAuB'
    'TZgcIA)6vYSBRgp3v1rGxj59A$`~)Y?!4%%UOe~$iA1f;D?W9PaZ}-3s%M!qY(LezgUzM#oTI!LL(+LOx0J@4ezI5}*tiJP+dQX#li6Wb1k}}f'
    'uVwzWtZ9%XmUeG#|Bm3=cazqeyLW_^UC*%RbsZl@Qf7N7SZKjDx2#||0ljUC7eIm5b||`Bbvq^WtdcpLvMIFmwR->lNT}1+8y#<p57i-v_ML<P'
    'Q|+e2$2gu5y+1#7(B6YWs8uU-pDD1~x82RHv*ANwadQQ@M=?S3M=tHh8MeIEh<DFx_!`Xzfdltvk^WOtd-8+FHQ2EKD$QF9r&GsY=+K8yRz0P2'
    '4VN<e(mMWo?ltPuT958N`&4x7Y3BR2+qzWqQ!`Ezc#yZ_oB3Tg%leMGa+RUJMQidQi@R^xEpfZ?$$Y!A%ir6TUNK5@Ox>btN(yknL%nsorIk}k'
    'F81K*bem(0N7F{-FDM3@pffjC?luF{8M^9aSSWt%=4z|?;r6*8wcd|zl2i|X;<6jl@D=}>v3nQC-1>-2ZzbHnj`H)aTZPW&xc>JM_IRU;c&}bg'
    'JJYzT0P^Hyr;QVZ?K)cBFi=dvX)6{cBHfl{i9V5^1{U^IH;^x|%M|LS>mGfjeC%7OKez+md+peqweI1WKV>EHT-SKpLMo^3`D4jSsi_&)Y?L+h'
    'qAuZN2Uhy;n&TJ1&@*J=+XujJ^e0T=rLkXG<oMGW&^$A|Tzh6O!It^+JaU^>Y!Q3S3^g?-<5~-x2}}!|)|=`Guf6(&`p0YPc75qMw*;EcspIKh'
    '+FxZ+<bkp5SQoZxNvpQJ4=v(-8F1@6ZG&yy9!0xD!SkF3GElU_m)qSdt5**prI)jW(&pn1-+uRy_Tg_1NFJ1?ugbP{Pa-&74>25NeD{w{YrXpt'
    'S$TJEzQ#74b8X#6yX+T*H~E%EH}|fIZM>aDR&Ok0+m+9LHo9S*UP&)2oxFi;t;|T@Np58<!mbq@U)=9iW3%j@x@;AsFARcw9GU5=0T)+Jb)qXM'
    'or|yX$_;Jx&d}-tVQ~Wt<bCV0a9Z(&72bfMkl0I_2~U?D1y*O?HrA*REf=ciQ&L0Hs1z>l{Bsu%w)4Z}XOo9OE~uHNTPg5HWHIZG=kwC(4op=K'
    '@mGwHdnlp0Qns(Qx)nKM7k8MNHRWh#1VxU7m%}cr?Dlk>>EYwgXJla7s{cG6fYmOxm(F}WxE6PCep$lJYvp)~LF%0e$dU|z_g}b^^Ii{O=C)?t'
    'SkQg8=_B4#PJ7RqFZTbv9BoAY?Gl~u$7pejymN5+k0t2~t=Pk2$C4Cx5EW-#8%>CqPadDeSzGk%#a#GRo_c{6yw}&L?2jxfEf5Dnvr+Iv`T4RJ'
    '5=!yaeE-s>VS6cZ0Oh^@vaIoCKKsp#_Qaq>#?gz=N4RbMDE6MLc?zov3i%=74berffc{*|llEkVY<BR7W`w^i4n(ikFQx+oZSt6<Kk4(WRsZyR'
    '=65@D2V?X3eye{SN-HdN;Ji|JygAdgczZ+dhYrzb7ZxXG?C+~htz22IcU<k2UfO1`9Yz^{<KH*;u)hUgWyaL6lfR3G5lGx<$i{8@Jmcu}DGXlI'
    '%GPmTV0*P7;l8MGz@PPHot-mv0gMV3p>V!R`&{em-|_A>=NiWtITNBEo=%s)Odsgsp_k?#bL-WvqZlp^lot%zQ<r#xKQ8a}4fcsUjND|H`+VMl'
    '+;8`BBYv0Fp=UlGuU>bn-QI^ffxeUZxTQ6jP1zqEeNTGKLQ0i&Wz)ORjY`&BPojxl$J>`SiCBLZV<=k?NR!`$PgEL>uJ@UfusbSxPR!{`o3N13'
    '+VqdT{`sb$fRQwb`5y$Jj(A@WnZ7UR$(VV!CeUEiY?wq^HpsLUZG`QTO;6lcnXpQVG?wL}q^^LsI}fCKBg08t6Xc5d>%f-^J}Br!Jry&>Z5QUM'
    'Pf&|D-X^4Hy7bRq>@M=np19y#<1ihd`);H#0K194OZ;4<LH7v7Me>Vm8QRlph!?xw99lJdwPU?;Jgmi7g%^XiY~^@@Q^<2>|AxP?ejD&rGWbmS'
    'dTAV5wK|S@iG2|U(4+O~cJ{qi`@;(#4h^8}HeSSB=i5)HXTH0nK{5s__@OsS)@1|4wo1BqDs2$Z_0F{ToltMd4(wMgls@?l`i&>!?{9h(Cl?M@'
    'UR8Mc-d|T3W0#*b+HKB_LsP7p7_?$*^BSzbsoC`~I}(8(V`C`5Y9#|<#^f;mKtP$)3c_GFfpz;OX*PK7M>n{2I{cu~F)&u2_3$R0e1qg~TP~p2'
    'hu6*+JkRKS(RnUzlncdo<slzuB9xETd+61p)pT(j+Q}X?UH+m3Jm(ONJ4152hj2*f2N&}go9k@;Hj+*xhBOptyXLkYR<U+>A4Kx*IUxW}x^&uE'
    '@7VKY)sVW!W52zw*dF&7kGbVl$UEbe1)ESCo$12HzT0K}i!vcc2uN|b0`y>X8Nm`OHjV)7)=}nWn-`^l?(0a4Hpl1sUlV#0sxQ6A9XrTK5XYFM'
    ')r&U6fI=__ql(R`MyN8Py|$m$#BJ#(bFv{BP*E29l`O97$$VNKTIX!AubC({M!1{XPQ<pqyaWKF0ACP4wz=)&BJ(2osxSAvoU%vbmL{e#84cIg'
    '<o%m7%8K~$Co*mz#$;JjCL8xt0JUxcDcljm%1@^x^`1`70~W2z?N7V&ey)rQh8^f2$20qP0N`wCZ`U1A;x=^W{?Onfrr19zbg|`JJCe?&hDmjP'
    'PP#sO)f9-F?V`<0Z@rhl0-Q}#wnbT=&K6vs!shMTNiR{KAXB`RJ2Cz<;ZI>*g-Dzj56OqM_?Ryg)OHk_;o2pzT~DsaltE8Fu2AM3k@C*q=|I1G'
    '+ZGj?-GikI`56X-Hay*Y2Jc_TJ5DyIul@clr+d*8*vv0q?-!BXnyB#?f?gkBfKgl2Q-0l;EtXzPy^&1(ve(G&62$tA-!WwH9FoH?v!VOd?d0-p'
    '-Ye$YEPrluAIPM)?$1l9+M&j@`RbH)7+Qmj`g;y_zV%d-(dYwk@BM}EZhTVEp4;cn!R_JPJcuGe!LYYO@oZyp^s|IvUb_xfuiCKdyBgK84wLq@'
    'n69Pe5?z5hcnxQqI!h~mZEyCvPOC$qLssg8s_{!ysfzw?3N`CwBVzf-%KTG(Yom6XYaM^C(AO%-!f?deWd)9EScL@|bC`rXDYgkF88fWv9khdG'
    'jmQp?AwvBysLk=cg08l~7;Fnsme!Tq95*}lJC@<<1biGSlcYEd+VgM4eJFf^uEX5w#<_E6jD)nDSG|Q4*V`HP+sb%(IWn7V2bnP64+E|D-p#Wa'
    '(d=wlvV~tc;Rv9QU-cPU*f9n8!k#?FvpeY{<!sK20M~iVNJ*Ar03l>2xsgMS+BXT}H*V?4mJFVM;HkckEvwEwKbA5c5@Byv!;5=)o<HT$yfmk4'
    '`toI3wd@MG6u{j}=MTVY=|Ph!2d8Q=sW{uwWm%t&55Lo`Z2pn6xtMv6*}lSM<<DSVe?{^GPQBV$J4IQDRaedBWc^5x7Yq!0dH?6Z&Aff6kxlTo'
    'dlixEG`r?PudJ+Qmzv8w$Q8Zal-=?>hv&b8pM7k*;$*cuP}lXCRzS@C#C~;k{A(|%z%#NcVs!nkncJ$S?Y2o8a<%UW;OX%*=&Qr&*5yd^-wRV8'
    ')dOE2YT9*G_`mHe-Bgw9gIsi*Tk6@h=|TPiUHyD2YL!|!ZNBY~So_?y`zYI%%gaF^XKJ+^x0ImaQa^onvpjpf&pOckwqJWv)+Ha=emuf9_K_K2'
    'b%!)M-TFn3aAX&byt?E4%J|Wq0ax{6cHjH-33aXnva*H4x^M=;rE=xK(LW9|(pzTu-fb8D&m#2s$9DS{?SJ3>=VJjV^Af>DyVd*HB3!nf@dcvK'
    'FUH~#@^`m6VuL;@?4&1DjYnI!cXq2?DI7F5#F>k>od9q87hPMA8`XLzwDyzXe$Xig6xo;@zdcKOw}Edhs~dE=tlS2RcY%$%I)e#Vh(`OM!RHst'
    'vXm*p{Ca^!GYjB{zld1e_2LQe9{ioME3(w=kDcBg1-?|Bp?qDmjYTW1Gm~wGh;$_UEQ~+d*tqL@9l72?X2S(2wP&@W^*Q#zGKfo2qr|LbU97S3'
    'WEX{XRE~%TRE0!C{y^x{1c&{vzk$iq(WS;w0L`F9Fof6oi(8njhc@0JNxR)p6?tNv{KCJtCR9H=)GnPk6(-57Vb|j^MqhQgo!}?|eLnD(LK->r'
    'ZKV`j=Vs~BsaF?K>`F#-xw^o^1Wj3i!|`cy-XErPts1q2^7kCH<DWy(@4MAkiM6KHXyT^6hh2@n((l!JdAH6fC*Sr%MjR%b7DShJW8)lCVZ3}z'
    'R#&D>A(#VuzC`1fcw^-Da50B|5xD4Y1`_jK5Kc0gj}5ul;hlH+eG`s9us73B3}R_}J2p4mydhBsbCN;x;e_tA?+7VKRYYJ*x)3*Xx2-OF;W=E*'
    'QT@C=HFv+(VlFqkg(ft=9zixzk78$gbEb>V19_RFGQtmjp+CV3vk4_%SkB_1_&18Us?EM)^G_I;$JeU<Ug1V%uVsDU={|zGhgb6N$>M`mPG|Gc'
    'j>d7*zaaIxkZT3sDcO-YGy<aD)oZ;XSvX6IIitD%At!fWS)OG1IqxiTt0}*kQ}x7;ow;$NtO%?X-R9T4vf9ntU$U_AB(ZuttDU|FFu(j({&lbi'
    'pOIS`+n<*}g@igV8$$d8SFL>Ef5pTk6|x)5QTi}d_1wT|_}ZJLpRRPu2LlavIMqlVlk7ZCdRbWE`WZXut`jhuH=+9FCO_UHJ7-g-{<h}SE0LmU'
    'Lovtu$sf1c3;Hj-T@Ec%yFEQCU4!iWjO?&RN6FM3G>zdif}_=`K7t{HOE!(yaxN`#4|NscU5~SlHpHWcr3C<?&Gfy_u}5nIDvx&sWDqGDNK%(|'
    'TUxgpx3B(?U;0)f+<qOkLlsN%iy`8&7raxubtHGiqZ?GnzZt1xZ_?~-YRuX$wWs0iIj8yxtwc)(e`<8CHmgVGu-ZdNupYuhoi=D;|88HQz19Go'
    '(<?eS$Va}+<-^X&s=IlU=s9(QxTHBF?4^YFkc&YEja$T@5Bm{E|6-BBqTLnvaOP==uX%EI2*16|*2F6kgJ2Dv{S7}-Ced-ZT!S+CQGV@VyNjv#'
    'jX7RkO}uf}J+pmjxav^>=`QGHG|{Gu=}MD3ZeHvLf0dG<NNgH`Y1JRMKMWLf=c^8r*}kFW>%(2FEGyTD9DPsSeNkPacWSql+dF0^j!?-n;L)t;'
    'o=$lNbS}NXkm>5LF>j%#G+&H+A-bJvX=L?XWK(?R{rVL}Ui=U|G~o45RN&(8swztNn!@$HgEi;esaemKk3+MlLeS)m2Qx%ypndAq!l^qyR~BH+'
    't}ebvkUWp!;de9FJew`@CASzg-p$QtV~eMJHd+&iK3qkO&rUFIS$R9b@37O`5zgn;$J8z(v|g8M<KQ1DnIIWQXc|-}ac))6@tVZa$tI*jV4rRV'
    'qChmG`_x3(ZtnSoqp?-VT&H!}W#hFrMK`H>^alM2+dV;7t3f~=dHA~e{p;*Sz29a%UH(c8zf~sM1AAuJPB%VHEpKt}-W(muOWvCPMd9RnLwgb)'
    'UUc;&-Zu2~_z1(7sm}M#V;?^pHf@5d(H;^kPauDDnOss)4H;#WV&T((c+`RqbI%s!Yu4!;y6msgV)s`8xdaZWxqp}}ZrCZ<e10gUzbx8Mc26zP'
    '8K4SA*S;v@vpuWt3D`)?f{}$$MVi0q9ZOZGVE@sGe7yD>zuJxXuZdC}z7eWRI<GabW@~{gh<WYq?pU+AHuCZY-oW9G5wc?2D!pY%cZFT&4Gs@='
    'F~9XLukae2YN!D=C1cW+czk;s4exY)^zgPwYcpJk#3$T~)BNx;$xG5t-4Z}1w=ExUq1B8+kn()ap^*$FdMTxB_C|2Zfge5GrMu{#<F^T{G1lgs'
    'QvLFsXY1>M7s3dPZDKg>M?X@7_U5%ZhJTS-?IZ2SG+$2@DLnlk;G?eUM>g^PsyF?VTtFV^zOY|2N59&Es??LCgZ2VheZ+dd<6P@&J2_Yw4j{}3'
    '`Zig}x;dZAoOZ6oj}<bn#MV=4R~x&vBmMkR#@;y4a!Vr4Ry^zeM#<>0O0(+cq|HFMif<0ch@OqANWMGO{MEsd^ueGK`;Xe8hzEZ|a5n9wUQCNc'
    'g=F8dq=>~aqm2i)Q!c;fdDlD;zQX8O`mDi+!n2QmE$d;|?7RqP8wF<O-E=hFb(?*HUE&Z?Z?{a28%JERSyecHxcRN%dSIqR|Jv&t#;wELmr=-V'
    '-9z_#D55HDgz*+WUCd<Mt53KFVvjnB5c>6If||uW+5d%WM~U{&ESQG8&c(0uvSN2oc<^5Hvv@ST-1-w;^4Yhy_I5?{EV)cZK_-Bb+l4=yk0KxZ'
    'Xv-z<*`wJ&Q_v6@pWdHGHysYq#iwTf#2Py;Yc-KJ!*mk=m{_iCF5ltpks?M}GLMv8n^GhCZ4T^>;i&s7*yZ-r1AOmE_X@>%y=Qf-Yd;P=`)&0a'
    '^9%H9moL=LrF?h0L#F&VOm3ZXZ644xUwuF35Rq=2iq_Q#*XO8<>IPlH?ZsN5Y{NT?Us1a{18}x=Xzoz0wa5%b?}{PU?yXZgLF;j&5eX__bxGza'
    '4K93@oAp!bwY`xG6<eP?I81NNUxWI^+%6i&r^p-hdOuH_KG#Q}_MQT8qBi#juYy9?!hH*ozmz6JXF2<XNc*tqjxDkT>*wErn}drDS?g|P`LaT^'
    'X-x;m=M?(5Ab*lt3&3x~7&ulN=kzg4eR|u>6aPM-+q)XQu*b(eP}#nhW0psu23{GhqLG0byVeo;c@>a`RO7v+sU{Ui;U9-;v@!6yLq8kMg3+~0'
    'b!Rnkd|hAq{RGn~^l=afB=zItFzR)aUvJi(<YMc<9~0l+&go_CY(iJIIbAZhS4}M8=e)&C{tC-`f%dDrDwq&8#dYs`Dz*(wamExpFY3*lz_oI)'
    'g=&y9f6@hTO4jY_^WKm{=d?{m<e{}c+5M9{d)!C!N%i%7WsY=h)W?6b@3{hns|vaUV-7AUTiA4V<rh#@H+$xY+XQ^f&GWDmSDWs?zfq6uTH`4y'
    '>FHK|ZmwxgzsLJmkLmdF9gQ(<waNEviE~ApOdbLFbBycmQTj$(JR4ykNZnDopVrt)?#Swm0NzZE4`jzI4&)x9gw!?^jw3DZ*|66iu_}tOQz5dT'
    'HNF3Y`*1Wb`j2B$p54RqUhlM{mgcV82BJFlMrv-*Z(nog#*2#&lDO$TFr`G+qWuXde5%cqu!+}c-Pt4VAo)auM=Z?lW49S`(Y+}|_K+Q+Pkg>D'
    'n_&;HrZ=nE`RpUQ!Nd0%!BY(zYJi99<yL&k<F{%a;rQ0MR}E1R7Jv#LYjydH4!ZD&skfl0_~L}*mnHBJdc4@}L&?a!(ggphZ9iQCFMGEyPxm1?'
    'BZn|{ye2#Rc<Svo_4T+_hTjP^^mMKIt6nC4$GfL?4ox~fa#R&D=;?!ir``I{sR82^AoU7}^LLL<tA9CDxTt{|(cUGu*d1PZFG;0x*tEpYplsdN'
    '(b%a1!@?F<S728Q5%zl@JQv+EGJ&|>r8O>#V;_H;KY&|3sWHfDJ2NEUj=)qW@>m_IzsaPhIy0xOe^j}?jqS=;D`{E;&b@B?PCcy3A0|GMz^@He'
    'knrl2@b>IqW{b3uBA{G}w!`suSoE~#V*YNY*xZ*)l!{hOmhstkf}N&nkhZ3<$61l>t)g216TSp(_mx9y(&UuW{YDJ_ZB}xMkLSuu*kSTS??hSm'
    '-RXJtTN?BlKS5;yZ8MVF{9CI{pK7u%FuQlDs$+udp0i4@_QpX`9Qs#xf7;#n&3x2rzR=lVPK+I8Y9|N~CYQ^lnHP$Y-T%CU?=&Z=d#j>&;4EqT'
    'U1EsPJI;=KWxAO1?=`|@wO!vkM^=PCR<AJ>yg1)8cB%0lZU$bW2k$F}gqT`Et<A|9aE4<l$EQw>+!ubYf3I@znyC`!?TcL_xwvUie{@cU1FHpI'
    'GtECXfVZR0b%iw3Z7nVb$8`G2o-dqy6VUC@ANCIra`y@qj>LYF32VJ+59f^Z%`0J3%%GD)*T1E6WF!5gZ~BeXv6h`E5_C49nizxF-+HIPN0$zr'
    '9#DY&*jf3d`^~}8`dtwz_=~H@1pWUD0i*NXzx~_l`v0y4)c&mni0u~YaX`zC!}>Ups!7ImjsrB|M5*kgp==ck`l#*7;t30HX?T)cRfA{02~*D_'
    '%w5xa7M4Z6joR`ES`k%=sqTO~jP+J8sSMl+G$F9S${Ppab0LtY5Y~3to!#GZKpA!})+>Scwc(uK>-?oN=Oi(>xYhfm-Kr^hKhy!pMq63;!{l5w'
    'nzT_%%p{v{4hab9weqpmvMN#9=$(o$2Zs25=hXFAVcW5CEi5MsPcUU)P!N?Iv+U|VvrLy=Y!Nmb>Goaaa&8b={!-;(56uEh9?lc*Rc$_@0vZGp'
    'H@(e{h13VG&Z7$RO?&%7EuC>`dN`ed^Fy)4w!x{{nw^N}t8e#%g}Griqo^xLvl=w`?4*;etfg)lkb*o?$7O{&*3aX2#BzOePVnhzHhs%?FkH7t'
    ';75eb_Ssy#6r)CzAciekO7npnpI;Wc%;x5?cMJR>ZGL;_DSfu1w%KyMj0GCQdHwe{$|<e!oxQO}jSX(KX$!`$RVa$_y)cNz(PAUoqqn_<xtUU1'
    'twyie$w?zGuby(ISNG|piymh2>KM5iGHigLyV~V(GHo~C*ZwvdFU=<Xn;Gr8v>W8<^HiD07va?b9#iMA($ymy8|`VWyT3ZP^aOV$+~1R1G$PyK'
    'Sniq|ey~cc&0CkM&O;xpCwSZQiLe(BcfK-|#5+ERzI_>J_}a?D)tWi4K`*%XJkxK3oT9M>!tUe^E$wyMAE&c?!}6=-@=NhimVKkoO4^<g=(uTt'
    'pM{FBP(m(eFmKE@hsWW?lRMG(vyb;$RM=o|UH=G7`m`tUVr!o&kbXbuWxru>v>Mdeqh8uS^`i6!{Sqf{g2rci?o7@!J1ez{38~30)Ze7fktY$H'
    '3Cm~a7P-D}cA?pAKiSS!A~T>4dM16r%c-s-C%?0?Znrak^|ij)ZOZHy#s5tF)tEBV{KSlUySg^*sLe}Q{E``+8$tR2P+@~gKkqo_-(r7*i#_~u'
    'NrzY5{A2WXqpekAcuDUL@WpQ=(jux?O<4cJUt6`Q>B7RVleLH(ysdE!(GP|%Ap-r*UgQW~Lz&M=Xeut}yXyc_0~P&Yyk*-|dd4k8HRi{?qk3h)'
    'hMTd*Oq_6$z(!?l)s6B%u{r?5hd<}Nv+pMGZ#y;_fzjxhY1#h1^ODZ%cY{7&fT^c1z&9GlNpiN%$>iehZJd{($z%6`6)4{m{@n9Ao9e%pz~!c>'
    'Im7L1=U?38>Tu4(<^0^eiG6K!_;X@+J9-jQOWwCeHsDLbJELK*CpFRpf&|;=z5x!<Z6WZx<t97tm09J&2ozvd(s(J5PQwH_c%SuF;BmNmQ6>aa'
    'JD}DwuA89B2cuMVo`2JEBpvpk(pe^*U|#tagOAdxPxqfunuwizA?W8Me;~~5Q6V>yQ!9G}6Xdi2RPV~fT%2Arho1varP<KUbLS@x@bj-`+nw5F'
    'uZ=4<U>N&0ATP9Ne-^pQa4DS`{WK@=gORPoXjJslcB`NK7QIvBeZA!`u5n+mYF=5beeDRflD_s>Vy7CrkH<Y@Ar?#ef7v?M=5xKUZ@-p?n#!1~'
    'Jx$u!CPHXK4^&bp+bAWx_WS#r`@ubP|F0(o55%l>o}c4bs`c<!%xhweMnX>n_{RsdU-lVKAV>Rw7zkF9P0*>b=L4KfmP8%OUp!**dsVn-ts{8k'
    'QjbC3UE@<VCoU3(yY19U2v8X>x(2~jD|HN1hLuy+TS}kCPu;x6XcPM0SF7vmCdoE7N100BrRLOh(;%*gg&rh@InIUSkTGGDM>A8DkZG5sAL&}K'
    's+5W}mUZvbe24S(x^G1XwxwQ;ao)}E5*B@n5n<s~r58<xqxh8@L~89JtWpTaTT!Lfjq-J*tRwlAl|J-->G(-KkNw&d+oM+n8=zd{qJQZ*CyL4#'
    'Y{}<#2pyKh)m#mm;z@T|?ebU{aA!i5<C|S=crr!$ur2pq^A@6vtl+Hc(BJ_ArqY?tVNc7c>g@(*Q`p~m`<HVn`iJ|D=nR+7S7pI1mz14J7rkKC'
    'gWixNDWRqf9$7sEF|h)UlZ&9tYp#l3<+~bnv8u<est^4VuuEetS7*yvdAeYo!~IbAd3la5A@F`IvCgqi7GDw$x}m?oU&wO*5|fRYz6V{Q=k|hK'
    'V2iVh+3}LiOZ2_<!v~Yt>Sj4|a38=%()!w)wGaE%fENi126qq4TYYqOv398H!?oi6=r-)Q$i{s)dyAx$cK*EEtdE_J4d1tK0ypI1=q1~6bQ_4#'
    '$ioi7VAI?Jj?bjAQ1||XqLVuzZ$8%Cse6#*>9pq>7<HM~3^!RZ+Kay;=thl<5WXaq+}7L4@;U0W3gX(&<fVHY`xlr@hDV(Olq=ogv^<`Mztf?m'
    '--Xtnp1|4i&JFrQC8;&{EkPBS4$a+nVq*-*;Z~{38|T7<dy=+a*(4&lCkyXBjYs>O_RWN`E5|onn>4da=|7HFrM$WQ@L+z%daeJhYq+36s%kF;'
    'n9+QHvDywLW2>wl@U|J3Bm3c0#op7HFOoJtHHPrwy?Q>fY^3H8bo7<heRtt}`;b@8sdb2Bq;}wW#6*9cl^G(h6XwP@EdHkHvFZ=oZ5&&?D+O$h'
    'r^Q+A??_`~b?oNza=Y(eo#pmED2M}Q?R)QN4-H9b==g}bs|4nJ^>N@a?F}V4%<A)W@a4^E?wWsXA5Ur^8#Re%Kd;u`*S4jgwVmxc_4xv)*xyo0'
    'JalM0GF+D?ofpWD!{|DjtzhWjE{{?3NCDmD(htL8g1+saX|}}kR7UWj)gkTJL9h5{s4=ygzoU<XC&|PUbjPFLhS`z>eAjXAjB%#Q#l+uCAbOJ-'
    'KjK_Gs1SFeU-Kn1j?gMOXj6}_`tICI?E6;7obPk912T_1T|`KK!RZXOOzNS`$A{)d*De_P{U!CXpLmZ}642ITyQYDv`%nh#@4fYO|H;TuK?gv<'
    'V`;NZO&dH@d#QAut*0*sY1W>*-%g#OIC57n*oCc+*XCkgmi74{9>xD<-%0QXPXGB2Y<=Wca~isSN88y3odQ(8Y}H0i)T;<aqd~MUuXXQq*oaI0'
    'nPt|z#vHd6$8Ye9xIKjs3!J?4)ZvZCt`1!C$8YUNgHk1b(|NLBd->@p^Y@a6yA(--oc314v?dV!o^e-~Eqp4ZA*ebdw-giMmm5QGo=Hq=WGpqH'
    'mk-64oNkgT0#)>0eQ?;q=rT%iY2>a{Vm7PVJ!M^$Ccj7BS?Ht2P{>-&`FV^^7F2XL*y&BnO(v``uiD@!?U`${_l1!w^VHXkRI+NviBaFJQexNY'
    '_tRgvjP^!Cq<P%8z=?cothf=0Oj}#`FMp9?>v7IbBk6N^l;>Y8b!X$#-s8o^QB1a9n>41c?Xpk4(og8rfYv10=YMw3Z}k10?C&(;9M_6xu&Yh='
    '3ov=%i+%;!R|HL6ye6etROQB+kH>#5k6rH6;%AF(Sf!ggsg(`t?8An289IY<`|EZm)Tu>2^X`~9$7IiCHp#-Tw1qwkilmV)DvS5$h||FP4MEJ8'
    'og7cTzJF41vtqZwCXYjt*J`npR`y((M5&=RLV4(|=Kj2Iw=dVLQoPS;ad4ZRT#SbBvUl2Pf4MPCuKlr)_htuEt63)sqHgtCT{C*EHQ<C4_Tz5Y'
    'cn!@@HdsH6MQ7T7OezgC2hY<uuGgoD`*ttJpJR-E@?T9Jr&0rl5mVfQMCgZ;jgg*^O_*oA1<UfK^*N8=*$cw|)VDLL8hfGI-Xn1_K#5Hj=wAG1'
    'h}Cnf$UR9B`Eel35^Y9*CtCohHHVJ|HokQCP<=!~Du;oP(^B60_Sb9v>3io`=)H1>G$jYoKSua{wPx=lP<VRf01xYf^%K}^%it0IUblQ4cg^8+'
    't$Z`y1aaiBa3)0D3(K{bEQp|E0*G1fEm!qE`A(K>x&uB=U+m0~-Tgq#PHv04#il%FG!|edmBSOQ$CCvu4xpvFgJ|!zTOYu7ZQ?DVb43YrR+0K2'
    'h-yvh_@{2SUOmWaEM*)4qjZAf<L{*g${pX|0CkP6YqN!3hwg{1P2jKH4Z0^mv!w`6;{6*@7x>y-{N)7{i*~86&ACYIPe-#(tnSrPSQ3*#@h2ds'
    'cL7$*xLWngUa8~IZR_2^cU-5>Ja}pP>}Z|z;Sl@8Kxf%_qF1b6i=As)yNbt9R*`bC+%Oxo!x{38JUfp(lI6c%H+7g5D=d;~FUR)Zu5kZ)D@f}3'
    '!)B;z)^I&J%WW&*(P*cwdQfmEs*|MAW6itG!1eny*Zo?u=ntj({hW)=_p};R9!&b~L(9i6Te&4uZU$K&c!gZGJK}EvI2`WLHZpi_b@A_5v4ww@'
    'big8`dJxmNvcKB|{9Q}+vN@`Q^YzWS7IgJl_s<@8A1t0qfRBwn*AAz(3Im@l%rUPqd)Z%G%4R%UEM>Pnm&^l0s4QMHmPk(B)e;-tXusm$FC_QZ'
    '#z$NO3)E8Gr(R|8Tm0Vb;RHSrse@eQ<~W@_s_rdn`}H}G4Nte3c&b}f!JK1oYJtN)ug1Qi75xCBClVFWzk0miR<5l}mAgICqxl)!My%l<#%beX'
    '7&Ys*S$+?C3bxD!Wqc@QBrND(a6E(#jV=~*PptjDtZJ{}EbDW+VK!tU3MXu`N2bbgVQia~opYa23|!a*>s`Li&tsxj_L&@otEvPeLW&<qFx7s~'
    'blU9MR&x6bDMjvbz2(?zc*ay+?zWYr>JR8_r$6E%JA?C`?h%in=r|~qUH;_t9F*%izw)*DX6wZdF6x`h{p?^TzEl2Svfgh4zwu!oU*v1rHuUXX'
    'F(r6h*Rg4vqUtuUEwW1DZ=Kw{iv=*7VeR9n$b}{I1oO>GHdj7VyRE_IC6pbt<xFeTt-BtNLuJXlpmYk{`ST`SaX;&BFxFcqPmhZ>F)rO6@r7TM'
    'a~X1DqN`j>t@z`NPEaKC)VTD{d<AVM#$mInDAMBlxWJwoPRW~Nb%sNN8q^dxc)UKJtm#+q`&GOtu6@6IjEg}ML{dn##kAGE;$1wH>&9y#e^*ak'
    '^gHUf53|uu=d-7BYAYW*dotgy%dxMmbo)}aA2+auAVWB!<V=)rNH1uQ>hO78dmt<qMUzu}RifF3ElM?WhXBM~5v7+4x5s+T1i%XcGGyTW#<%Ta'
    'I{0cydFAK$!X%IPVqDqpcUfl-K86qspGVSUO4Jvh3S7U~TPw`IYtWk!y+@&@#!rJ#0hfqM(goJWu{L&3!|F*}jq5bAgK-+kKC79%ug~w-ao)l1'
    'll=ZiI!W}xs~IK>?7oeBf`dN3QC-ine*nzSYO5_#Tg6}5{V*Vj58Acj4z*|4>GM_E<C3tdz;y2pZh})&sR1k~z_@*2f5Y#?gZv(ojaqm`rp)NV'
    'uA2e~KCRj78Pue;ukAA8CL^umU45Q71(dj#9oSERW-<<#T!ZHySANeEXou9oDI=2A7@5n-y?4?5<7hoxfk~wum^j~*X6^m3?A3rTRw0sJc1bg<'
    '*cN@5l^$tJZ2#=d9%NQLH7k+Uy!wu@w|zPcJ=@vO8_KHfAE{hk&wAS!vW#la?u{5VSA1X@CPRJOA@nLBi<4q8Zpe*SM$c`&DO*4B^TLoC+a6fb'
    '^R@?P)Y(3?U}`d(UpL9HxdfzdRmeswhc+DJ2}G@6kM{b_)*EeUjBbM}V6JZ3@q*r}&wFDGA&zj`#V>;1mSK~uk7m|I`oXS*?48l$5r(skIsLQC'
    '@++#VU;GOac+r#ld`GJR{B{kgWSx0ZO(O4m`vx=t!q6~XF|S)@G}z3#lBrj<r&#s;g6Ho2%4mHolRB$9?bq+9L7!yjY!wegswQuRty$+F_S3R)'
    '66Z4}@KNm^MXU2087DPB8FSr{Y0#8q>pr>8hS!!*j)lsn{^?XKHCz7v;Bi3R&b5FT%+p?Za;G}T%PF@YnXEtBaxnzgs{Qr?7(;mQcuUYBsh$}5'
    'Q4L-|z8<T`%bd7*6{(fv>S(=}();2fKF2@b#Hw1^V6J+3*NTf;<>|_`fLq84<)-=U!aTgU^X%=VD=E!POjGvUOZ=O2=DM^_)#c(O00W?FaZ^WX'
    '1>*^J>+UG;`M7&D!UjDdHOO%JR4S-q`n$@J5uT*}ahV=<pMq5Z8DM4ZRZRvw?rlDMy2lnBHwSeUeV+Z*<?>1iaJ66VzH$BbEt~eS%VGQW6_6~0'
    '7MS9`UM9Qxg%(YEMx&$sg<EgivstCR={&a&2LRy@v2iLB``Ovz@Z;Fb(oVNKe-BPO?%Gf)<oTBL$DPH^H^_Yb1&upu54f-}y2ZF%Ukw`5jn{p0'
    '>f#>8x5y@UX=WQ!$MQ+VzB^X{>Q9C|4y>@cGHf-FW=oD_&)zFLqP6vYHr1oX1koHk;WV<KS^&e<S!n^b`xu7XtMm60C(&wmGKDFG8cgfGbCkzT'
    'YrPM~rp8UWi-d5l>dfw+cbNP(!+syj>ynP9I!Vp>xhm8gkwRaZb?=_1X^2&FaF5w&w;%Sh>1}eT9jZ9f>-~Uwwqg-@d1cIp0H{fLVL`IWH^-Z*'
    'yK6L7%m<UFA%{W_bTohWuUlVil4*3@-2(LhKcuwd6I(*>YPD_1G-i$BRpf&-Qjkvb3I4UI)S=-6+TLsZdiU5jrmlBZn-9&ycM`U##(n)Xzo*a2'
    'WdSGE{O?QAnAhHNN@v9eLd)lIub9-VLans)vboFXEZFCp!w?@ubuTz2KX_Hy(jmfyu%wIMk^<RcxM<i7c?i0XWDgG;pWU?E*-uW*zxQr}XPvrc'
    'x$`RO1aIlb8M0{r$Rc1XH+kqx!R~+-H71P@*xdp1)N)$B-!RZanvXmE!{`22Xt>>0`-j`kTqE0x*Wu4NScBu#lhU-UNMy;@<qkEZI=lL<te@&b'
    'qB7xsc)c(5uqMXI=KNag_5t{>#iCDx7|6{Iw|irq%bQWet_%JdpRlqDVn@@4Tv@7UVe;84FVq$@)@9XQq{;VIWoltEe~THhyPRrP&hnC8<7QOZ'
    '*x=AG@EUG!oZ2@ylH49cJ542XzR|5eUWu#MgShaIyB{~JW|w}=M>D|!w9q47*vpES{<D3{mgwG@d|O>PgABvlCr7zQClf36w$tt|HgaG*R;s)O'
    '0He|IjGQQWO57~aXc~R$^zohZgL+oxj{zLRWbdVc5BYH2q-d)Lo4rT<eI@u9KSN*lwOt>*;L$vv!G;@9onuA|6|CQA_@~aIJ+ne8KLbQxf^Pl8'
    'W>5a*m$IwYbSXXXr|X}$bfMuvu3Uo8VX%ar?G@1Y9uDiFWkY&i%>Kx%yQsOG%;n`=nADow)?_bhV|SizXkHADbN#WsxL+7UTclN4&>FVZaErBC'
    '&svYGsPzlmA6S3xG*wXgx=l_7bw96USr@Tz3L!6h6l<Mxz5)q;lvh8v`isOxE?qnKoxVD0uG<q|?yT2Y-70hO(+YAIvhMhQ*B0jK(U1TCwS{`='
    'dl!&~-jymqKDqk+j@vDtt|bn8Nhz5q;wKeFl^zW`>z2@!ug_Pl>fls;I-6Pt7$0L#ni?qWx;9n8?%$_j&n`Yzy=^d7<TH%~#0S|11`;UqU6;c-'    'XSo-)*TZVvAx?|d0<>L0>Fqiua{n^5-SstwaqO=gZX}sox2SU(zdFm33zAo~;kxk9BwtmR6#3mdf$v#u_HL5Q`@_JZL$_mCP0ja&adrLaU}L{!'
    'ldyepdNZ8q#<hvbiEawr?r9?k_CzxzH=ScsJ%eKc@08vb{501f;Z^8z*VZ<79Kvv5*ud0diTcNSyGva6(QMcKj*ircoizId*M3+c@NK0%vA)RW'
    'f0N(Nhz+9uk~64kZ)|-OYpvNS383J*z4iC;Yy1STSK0t4H@4sCt)KdHn^%xC05y?8kY3g+f?01>_r2;b4s0K%^QMMxnIRoCjLp8)|9aj!(`NXk'
    'H>xhJ<Ev1IP01%m{c9}4O>>gP;Ch``4(^T8-_-({gedI)A(}nBBH7<qJXR>(z;+#)KSc}s$6Vig{54U3i}e**<?x;z6Z0yH6Iuq1mB>8Q+_SC?'
    'X=rU3X1pkl!#|*6a-CWAaJd=_!g%v&kex#_w`8>dqNpmM@Bm#T6&X>y9xy+KjoIN4&xl~pf6ZJNeP=S9&oad$yLARjg6l7FNw{WFJqvD#dtkaa'
    '290jf9%A(NIlDW~Q5W@xw-(ko%<B#RQoRc>-_Jfj(?#xwkCj!7{LqwVZ`FhDK>UZgT){3s<R<Gha#^k@_ufG<lScp5tl<1ZM}w;hO^1~cF;wpZ'
    'r71ptPar%Y&DA?zcFx-hUO9Yme4UC-B)Yfix5xY^Z6ETilwWvf`4f2otte%oq1Il*PKnbsqE5Lx^|n~NZ*IVIJ1=@e#yqcK)L9uF`7>KlOLU9U'
    'wgxqimCqUBCdk-84%hzN@0wp6Jjmlx>IVmZw?w}<NiO>)a`DcZ`hFXF(r5Z=HaTALc~{wYN^(w}UoCC&tq#JF5~nLp3%R6kT;+<9z$imQj()vM'
    '4cv_P6P1EfbJnW8>rnhT%Nm&YU&ZLqSudQx+j^)s9D|)y(=Aj<)cfZ6;r=ukB||d`f#I%BWV3bqvg^+(*t}_}?QxU{D@_K?8ui9nFuJorWiT?r'
    'Q{45J98eD4mvd`f@2So>bPfF7&)NjkZxsHu^?hrTS0{od4D~0tXdw<pHY^;I;eNE-t*_^5x?6tI&9uwht4R+8-0z9MoqsVFjDHh>(>bkSuO2iE'
    'eZ_o8FAm%?M`yCXUT`gRDp#S2)Y-Yy(cX!Duv~+|a5QbgYhuCyCN4YeHr5W9*Zg=}(AD;I-7BQ3N*@-&YGJ^m7S?93$et>j+JM>2Jk7a>cjqmy'
    'X|ornr^KMf3r><Ns-?$AxL>jLU3<LP1=KWoz|^sboq@9*3?Ts0SQT`s+ew<!^aulqD8|BGknI!1el=xbK!3J03OM_USpi@fUps*5Ua8N?kECbL'
    '?QhEP+Gx~e#<~r2RBe#`ZfRY%JHT$J6a&zd5Uip}o7)`D>^aZXqVfaZS!6x9D@k*5G&poXF~SBkLGqe(9e<PiC<Bv-4HD$@s%-u=US&4ZejAs^'
    'X00_^2kQYjRp-H^`e)lc+1$H2|E+$)aRr@fzsr0*_e-V>Xt7Z4%{rx8OwF@L8y@SU?Lnul)qMGYWPhj}f552Y&3ALND_G5)vUpBv9shdpgu|wK'
    '&d2UPTN7&95xigcfmn3SW%!->DbSZy0PD0L3gZ{wV+fmGe6pXFhrm1vYmct(gr~5RwHH)lX(e6!CgGPucd6YMXI6MP+c}Fbomor{QrOD0+p`Yf'
    'Go2p-y>I8JfN&-4(uXJ5w_y)A2SnVsoM^AITa;T#%yevCbZ_2wKX`W07TR}D&CfH#n<a7ZYOLR$9sZ2w`|c;>dr#lqw{z;ZaK*XX8jViJ#JC%0'
    'aC-#T%%hhMtImKu&0GCX#M<gHW3tVSU}pDI@5t90-}oGH!x6COgmO<Wud`(#EOvHd)eQRw$=HGAE?x8-TQrINw*#>9(fP8^Ja}I!Gkp;(z8u=_'
    '<{yNsFRu&S{gaS#zU$nd*C0q=o77yBlrG)w%~pH1ijHN~e&>==w)|jfKG)s-1rtQ#?|_rzIr<g-=+zP%c=3E6Dgs!YZCwe10mwnB)$1(6kAg<#'
    '{(M@EJ>r+PA!1WybL?R9txY%pb!!}*8}|(U9It04k!O>~jq8n0g`Yt!!B+1GHGXvFM|Zy}wi{mapJWUM#r3BAa395!C6^t48pTuzEqU6b-zvM)'
    '`~~@iqqO7E9JE=ceDnT9ieH(U(e7pr*k46L%ZBo6{VHYqF#Y5DvZt}0JIxji{0P?X)a{K9iY2*frgEGd*oEO;Bw^CW5A)z!fJ2}%Gl-wqk=yFA'
    'E6rNsVu&DO-6qzmx-($Wx+W5T@kgt<dEwz#P14sFL9N0|DqP!1Fzy7UZp`auc4?y{0JTbR(ER=yUry~d&7Im>E|7(D{$<wi!gc%jDQ5{PnghS%'
    '`U0MxE{rEbC@2NLCUZF4VHXXJ+Ji_B_or!<y5Imf976`vOAgzWhD1)(g}~vJGV7O&e#_Z{T43FuCe(~E{5wS7gE1Cd6zfm;6Y_PA^c5^WP<$ZW'
    'RM%ux?6RMTX+Acq(VX9&q?zBXdtcIOX?p8}T&V;XMY2Da774q=1~IRvj#O5g?~=8%3YAX)G%{7TvBIl^0r>8ORCiUKUCzuy>rG6b)1*h@Xzx3<'
    'ruUcW3p#6~*K;7b62Sf1*Rd5gAKfc=qq%bZtsOh7OuBqO1LQ7b*J*1kw>~D>eKibcym*1uWZP1uu~eny)~*4t(O)hU?YcEB+wJXG&!pDt3fI^0'
    '=R8R`QeZ04db`9~WMb5k{1t&sZaV(W@_N!R8}tyZ<{0AHZF>GA;tP2qM|xDtCna-ekr3S{HtB6C<I?4~->l|2oTAum_8!))!X`m)Wb5>^ffmY0'
    'pF!v%N098Q{qa>jx*SqdXy0qWwFNTz2+iKznnZiMaq|$jGpzYxH>+0VL8G>ilh33%$XAZ{BAUbMW}<5W38_=T=u+Qc#=|S|yn{Lul<0ZG)1ar{'
    'CH|)Eg%^@7$`g|RDK?i$!e$IMW^czck{WH$Wj^`FZ2Msr=Ty$OI`@S9j=pY>Ep6Aj5Nw5<Jzk&R`=v-yecyNNJps<mJ%f|$O|9<TI~aA8suz<e'
    '(r|75vISXfN;v6j#P(s`cM)PQ-7@;+H0BnGtWD3ov-BREEtDR>pDlB@?RBTqfK>ez{YJaX?XP9zUpBc{x*^YRLVt-(vOvHEQMk?UV=;>Fwtqy2'
    'rOE)!$srod?(U&(uAs`WM)VDR^^mD~MN5y}l~0jYV@BLL%f_0c^U``98_&8)$V}V!NAH7)J{#H#IWt7olh?8oyKJ?!bNGpvX8Tx(8(Q+xJ~DOy'
    'YaL!ec=z(rq&GI2b`&Z)1f;!7j(SD?lhQrmPl|l7uOE{v<HWN>wX4;cutOtK=v0b61um<hZ~sIi9rrPn`Xx~|9*6Z2ak?vDf5+P=1>&^GX--~('
    'P+bV-a)jucZnfjYeKJ@;<l;o$gl!x>TPi1zfok`MgGsg?x?HtMBJcjrYc{!piAyi+0(0&=<+xRaJ=^kq-}`s*o#Z~s+i(E9qCWaV#1li6?3~|k'
    'ok;Q;QXc07-rqv{{(UZ8t`^HAHgbSb*vYeZXUzj&a|1O@f?kBY25aL_|2}opY@r?M?S3hwE;3RV>8i;^i;-5ToBuY*EZ)t>qecIwb^p}wE<0`N'
    'cKw^%U#{AQsGzJS{xcR9EW}Tn+L^EJ!;D+?8jA@ZH21su1$36g{9tR9rhM)5fKiz7a(!)Z*tED;_FGvu?6iZEhzH0BcFj~`TTrH_M>{Y`O2Ml*'
    'mBz})-_No`_uobRJlH7BK5PQwAA&LVNbt~NFYxL*)DMcJnEvHdQ@NP=40hFRIS`4CSkO6JdAHsxf7#hJ9`oCr{<R)tzr(X@-PI;<NgpYKAau<&'
    'Fkr9LtNUR(qH7%|oAomoQ-Z<#QSl)#)lsTs&gu*%!Uu=&{j+_3B{uvl+2<sx81XR7Q;jnBdk0$l@By=LG6%wxxF*uIxRF5mDJyzLQCT-CtJQvh'
    'vBx{-S6oQ<20QSN;95<(6Gm5`Q;0qdWt(ox(d1gmi14WVwmywWte%Re|6Z0zv<EsgXFt=A?miCbUp0)T`xa)6<|MFA+^*vnZMIs=+vGD|NnGXf'
    'rqMk+J4|ZV3R7!}@b0{zmYu(OmRysj>WAq33<$SBzUN1Ob^^%1$fs?tZHH1PToU=_kp^|^N6d~-mrOcKbTVbfHR){gWFll2o9D7jc+9&#yvWPZ'
    '=8RU&PkqP{^RVum<I1HSH)m!<E7e+n8lQ>dU`BS0vEH>9WNTwd8_to*v>-QyDLyEbCBS!rA${?7RI%u<{us2Y^nxg>ztC+Zi>PZn$3s^BgQ@1;'
    'ef25;$BeHX<g1Jx68}YlQ+V$zjiEbgNHbZ1qVV202fKe4AvOEual-jwkLncba5Le@m$Ef}v|zpE?j&<|g^orKbExreTG|`wT^{8TiT5w7wnU4I'
    '$8s85ZS&{Py1PB$vN8f3x^;b20%^;RFIBZdlwuFvsWOdisX4mB)}ymHJKqUoJZUqBJn}a6I~fO_#aDi#`(Xh1*o}17M0MG{f6c4e{sUc1>h&MM'
    '9jQ+}9?l!h3kdYb5`&9uE!zb9D>$hLquC4dg1s&%oi8^z5xg$fo$}Rq4S;&@JHi7^f8+)EAv@`ikN+&mO_%%7?ETP8(dqeNKB)Hea^0?W##ILh'
    'g}{6UtK(5wTL8`5oHslct(^`B!tW0``?Z#|ZZ9)^^=S<kH**3sG2lIaR37U4`$+ilY6X8(Udu(Jyau1!i02BB<=3qYPNq|+H92(;aC;Kcb%^|a'
    'q}qFeR)$>4mttyM>t$JK4~{?YzbjD7;1u}(J+u4&-f5?g(7Wlh2hi(J9qa9(n#F_udNM64a@fTlk=SHbTg>Y9s*Ei3oZh?M_zS=7AV1-lZ4~Dl'
    '<Yp4IIs1ueRYV~pyU=vp*I$Hd-P!%=Tl*uf;oumwXn=hj7FTaaGC%tedw8cS&KGgeiWf+|aL-}z>pq0`9(LG**fnnV)@Ocj7Opq6^gLcDX-=G<'
    'ZFZ};y78P#w%cJ)_ggkT!RVq>tCjUyR06|P$O<u88)^?Yo{qDFF<ovS)fc?vhze$llhNdSy1uYJ{j>31{OIYHi9TkH*Q9>)yQ={e-&i+V^oP&9'
    'RauCa(Z&zun|d(C6QWZjMy1v9c5q(`!c(gS!|tSXX3v_FWexu%F=swyjNZw+!quBe&tY}OXzVkho#F?MQnDWyv1iwYP~ECX@bHhSz)3NwfKMf@'
    'HM<XGj?zsZn(3^3zg;fVnLDIrof}mfKwdwr5aRLjsMZe-L;*^kG+*`ulVo;SH0?|6&Me45MBtU%zSRrJPq!Arj`>jDiSoo0bNPmX%@sv>=IE{K'
    '?RHgpD|g+p4vev=h7DlP|6BR%67^invHg}E2jLYx{Uz%<kdbitNp{;yNTf4i0qp+}GIeAB#6_LUBrRj5!NQyDyMCbAcCutASB4Z_h?qj1b@jLz'
    'BrB8c-=bX%gjQeh)~msukmr5nLIkrMku|CP`kAf9;dA|gqWU{jo)Nl)hP7W$y%j2%H8g;<M|2}wi~aZ5r$!y&$QIw;`SB~zMg`erKKKXSdGi%+'
    'wNQXZ-WgKK6)+>HMa|Oeqvb^lcl8U0!e8^CL5SR$pJas1l;=n*e;~2yuT-{+UjNMXz{izv`y}2#>A%=rZ$>tls_wPcN5fqy0=Vrm$AdknYjGa2'
    'a-DR@vWWuTQ{GIW=Am(Ec%EseW9H8OBvnDD^u>Cs&yMv8*Ur=2Uqf-<o}ap#q4L!PHf#5n^!5j`ud}<8x!G#sL7BVOF5k|l+oPED)ZId3e6Y8N'
    '8f7Qsn{J0h5A^}I58vu=|8bJ!P6y1L*|j;#n)@MtsQ^}6?DwbSqLp#R{>(3^>FY%{PX3(0d)oou-t5xmGJB3#r2D)!*NDWKag9ATR5J);J~Si<'
    '3$*)4<drwwacj|}zjnd#r5MU_C;@-8J3osx=5JK?AP;Dx8N9B;R}_Z7%3=Bury}o)Bs~M#(P$9D#N^xfBK7X2Udif&HhsF8C~fA)1`y4U9}M{!'
    'xAbOd@r`C)--reY@2f{s*_~s)`i>q$@%t=3cf4kV5s=h(WSa!x-8Ef44TU3et)DM$(X^lc(EVhC-I`_g1C%VbV8|J3*`(~CJ1L3Z9RYPSXSj>&'
    'Ql-_~*p~F1T*UUaH>2^7_JVZecV(A4>Dcja+vg8u*J_+v&%?Oti=*3Q4#vuMO*PbBwxhf3*9xmOcVBE{>-@CZfVW>jRh%p)cUTxcB0G1QXwPUZ'
    'yr|N+R^4D<du!LL*d7hybTpmxV-Ygu^m{2(y9o(6UicWI8qG)d0z8z%?Z}-Lw=tlpFkU<FEc7Adqj9-J?Agk3#sl@VLvHeU<(!F<a$V!_vcCxb'
    'dv*bm6`g&@7;?0>?xJ|Nk=44tvAwh+X|28k3{#ZfwpPQ!E74?8Wwap5Q?Y^NWB)NqHw0pn<2cx8?D(u8TW~d%R7dUST@O!?s!aAnjU8?cZjpp;'
    'i2w=GoCRn2Ty59TM@{&g^T~sH-VRj`5$R2w2DoV8BYnGnDhIH0n;kXFO1u8MZ~ChziI9fh{`g(+i}=SO>?{YwGLmx&BGzO!$kSv01Fj9ks2)XT'
    'u^pdCQfBPMr3z~*QVPz8j)m_s3Tlz~3G1zqxLVbc2;o!<@N=9EvfI9B;xpF2MhZ1E!*v^%mh`%Y#B+kKiEj^ge?|&-a)^IC=$qy2D(tDa5Vy%G'
    'jGyGFH)DbWFC8MZLsKfow+=g{w>&04@jB|0Dh#VdR=bUaQT05ifSfV-QiI!|y}30{4&_GM?~>U}(=9$)snyNdg5U|!zz5Q3Sag|e%sx@MWow%p'
    '$KJDnDt4<Pq4_H>-4bE9d3>IBZ;PkvQTUXNHSN#xtr<3Xot<dQ7xb)Gu*+%HbCB#&{gr4BwT8Rbd#=pI_|($*mZ{_~_3pK;dDoHAh9qqhu3YS*'
    '0o`=74?dQ&n<UP^Yo623#yQ>*z2@#U&#mb}Dhw~agVC&2^`upuZ>LWjU63MY47*KAo0;Ube=gJfR-N?6_vRxQ^R@UA|IKy`o<ITd#?*+hAE>?m'
    ')2ZJNGC)IBocA0!ZJq16?_RDf=G1R+ezvIW9lcj=<u`GM{|l`gg45~0_oGQ)*{MN`FWhJ;&T8I;A7Yg1UeONfe|EN~_gdmESpRA8Y*)Ues!VoQ'
    'y9@5LJ<~PA#xpPu@>-!GA)Qd82T5EfO)+7{B(Ec&acMk{QRiweqj%EbK`(J?wsI~T)E_>opK9r5-l-KSBm!@VS`AG@iYiu`dy2TUo0xl~kbT9a'
    '^o-$(Ch^&uzsc`La@zx}sH;hJ8<M^(-74q%8QN@M!O|wIT8;*jWs7F;_LLrP@n^PXYS45!Sw#2oU<*zMCHoMhQ@HO;w9cV4Z_jslt3jiqQ$wZp'
    'EZFa`$m?A@7y0*FR22-})03Rm>%)~be>&O{KC4t9|BySr&`m--e~y=Pd-b_p)?>Qwom<=5E;p(pDj+`T6;r!^Aa;mjh>}hP(3?zF#te6Dx%S$@'
    'd!SfAy~(meI+J%>AQ!J<{MSEAl6c&oK_%-^Exh1Z8@;0S6@Qml0u8pCLD+f&=L~FAo7SC9NBBDIofRuq4%-DtA~9W*L^@VD^ZUkyyY$*;-+9<G'
    ';G2~6y&ok-$Q0YWR#Js(HVN2Vtpwt<m{-(c{$|!Kl%NJvi2vMIBY%Syjp1l0f6#FHhk5B=+q9e{N+|+dT7uW#6`RJem^FUW!&1B6^6kCXGRMe7'
    'U3CvF1HV>Bt()Slhin+Qc9tUSJ533#DKEqkwQpPj*Jvk4D=4046idVJZM!92fZ^$ifaq-O827A(Sb;o~hTjd44t}XfkBs13>nI&*_gO+0_FWqa'
    'bg_dNxLzd6qAhV786mda`8vo*6zxmt^3<cjIq)^g*5Gr$h22YsD?$<B_BRRs)XtMBjwiscPO6GaL!YLhJO?n2#e4a!w7y08nl~=B)tsXLa44HF'
    '+lGHRzXy>wn-An<8z&>*^{$M5dd=GJa(+_GUTcO{M^VuyBP50H81pJC_ekk@>5^?Bz<Sc@quj<?O(!;~_q6dQCnjpYrx&yR9gW-LOD)*E^6hzL'
    'd^f|Wqpwt~`T2th5Gm&V%ewbZhoWrY1<Ad7b+|<nFL0(W=+8+I^;@9t4%%YzxXevX>)V+{cYe}r&+tdIgibqOv@fr0IlXB;abEA@*M(9D*w1YT'
    '8ANxmEIA<;`{h&|*(f!UPd~HTuzE|+!8>dFD~`(XV+@&1{Hq=`=XWob>Ysvt7;00s@i-(qZ@u=Wy5V1VhK*p?y7r8N#hjLbl}g<<)LNZe>t(uf'
    '_`ja|`74R~@B{ndb1gD(uW`ZFyKmP^=ylB2h3sstCv**gSaH!J5NzzudchdGH_PNHcjwqA1sf@V6&zM`m)3^jH5>oV1X?>PT)tnSwMqAGK2Uz@'
    ';Nyc~=^VD*-FBnk5MyrujR`+(u)+hKqhDo7Uu2=#f!4=TrY@>YZa_B~N{1~i{~ohfc8Fi}n>O&Ba=3}7)}<{hIFCCO^X|XRI#lJ*Dd_5OTK$CY'
    '=^@+hKH3MA%l-C>Qk##a<0-jPazI^Hq_H{cvm=CabH4Rw5OW0_U85r^KsP5gw4nrZpB~SlVZVQJtX3WA;A6)3QC5SGM2r|CyUi#r3KiDlAW_Tn'
    'Wd25>3%}yGgZAzcIrUJO>vL#bl?gg<bZUN`C{0e)aqn<Hh2*p=7xjENmhf7@RhD$#3xOKd7FRlQL!IBvD0iOT#6|>F#UTURS0Jj@*%+ghAx+TX'
    'Za*5FUc%j8+Mkr>JHfc#VLz+WYn2<XiO1+`s|`Ib5uE>4jq}!lm$l7Qx%y9hN&^M=sE?*o`An$6o7#2csoAM$l(Z%X-g_`W!y6V^npwn3^#*yo'
    '7U|{=5L-`95X+x76(Y9G(_Zaq7mq0e#Lseuy~qh*v0cuw_;t5&>{pNeujVW}e@O#@$8%pCpzZACSYwe;>NR$D04AGya;cK9=bsk`j*q_9?qUbc'
    'rw5*1L!fj{&aVwmbdEw!Tp?)qOnzqohC(0X#*V=bG~7^IE2uaR0iOqkHc|+aHb6WF5@{Ch?uke^Sc70lOV`g|GJ3qMS!IfHbX(^Khm&9XcC(Oi'
    'I~|%I6Wrb2C3JF+l}ZxcK+k<uhxf_l=qVSv-nZA?(J3>%K)PrJAfIv7-j9cM^zc)etW$JAJxvGvJN!woSzVt9b~N_=q(yAwp_9a}@_J{H<X4jG'
    '*QUzO8qXe>Ul}v3rWxJ1@(WLjUXXWp*(;}WQyLaZNyj&>QQ9wM_Pfa4XC7Xrd^1a6q;Vc>8R1RM{{~>3Mr7~+kwba0(&q2lG=}yes?YF;x+!hI'
    'n=MsH=q36eT^j&!O@&|Ji?gCfW5L2|Uhkl^FP61IcDi<)pne~!I=8498DV6SAZ~h5=hrz=$8BQbo8d0Y9&HM}4>8<KFV}5#PI6@NS14x$t~x6D'
    'g#&DTJq?bTyR>_oiY~PoT;hP}Z0jTUyUmJaWuASKmpDE}R?)O3=NUa!Hzf1L@`_o3c=Y=6w%Lql>8RRR!n>E4#Lu0nDenW~@(s=gH>-1ckta+8'
    'b#dd0Ow&(~`#nknb5LyCGCLRU067;J!nO=v^m-#)bTsLj>;eTg=E2mOw=-+k?dKo_2=hg>{61d|9I-p2Sv-E}edrk+ZtO9s9Op7#J#DXNR*ZeF'
    'O&#%3(d0I>m41egBOqI}<6r&!J2U8Pxye_mJ6U3!&WWM6nr3G)XbhpW`<qmTE?E>Ux7>fUeS=^`P_N^=d~$JaUtw>EGN-M>mqC(1?z=%>A9R|L'
    '*V4p*mLWoxs!2M?%izF}ez@e1e?-O9!&-^G&pBOtC<E&tY+h@7(K#D)QM^@qpYfJHrcIW|>)-Ub>|G%IULm(OXbcYLt+()OiZ+xx<1+8_uI&^P'
    '5g80cw6ameN;6-bhhhO*DzG?UVgsE*w|d$to<N1s$VN?;rxF+~cq}VgCD-i=9z9sxvJIKOAK%+J8&n$L>ZZXzQaZ~|H*Q6D>(z=@uiLgb>K#p-'
    'c`|h0j-By+EIWBFn4?M$51KYl)!v3NL@H@w^@ZwR@ZP(r-Mw?rGAp#{DV^t`V?*3wQ}L!w)G=#)aldZdhjHQ47yQUyk+zj>zHg}V5i`Ya^#-+f'
    '`+@MUDn<ZZ(BB+o?0mHbSMX%?u2pGRwjl+@^4SNSaw~Vg6yAGo9j$e1w|Sb?as45cPZk-xoL<<O(|82Atj(U~1j^jfbdpL*3$xj1Hs0Nw7N(Q~'
    'y)_boFV4W&pIMi897N~a0=_nU)*Sy4b{C$w^OsU~Nqt}71h@473b=U92b*;kd2^?nO3v?cz~scjT2jBzL&$Y)Pxb!hrkl98#oT$^K%FShPx+qt'
    '5YULv8*>ngcg>a3u`_v$j{AK-+ze;L1Jiu1Z2cM;P=LfEt*0hOn!vvu|NMDv0&LrIeIC))dSlmbJ#}4d7F5j>`r=aPZ06Zv%a7#Xv#%|OmtvP{'
    'x!;uLaP;UVUI78O0PrqW9ozpqxtQK@1qB@U?4o%jr_(?O`|X9&;Y&)NAG8vi&u6rMdO*+h9@E*PVd3OzGZ+pop*9`N+JmYVU$<>Z`<8iZ_FmiQ'
    '4CKp;B#-Sie^B&Or8*eZeur|oThgoWXDPG!Uj#3(WU%s)TpO$0YV^l(Uj*uhtc<uF^`BkoNf12#M?F5C*YMxtV-ehv;1OJ&-oG{B|7ThE@55GD'
    'zo4N+VSzCq--tfZ5d=AWsE)q>U74z1x%rfEUC_tg{q%aY7Wr`tz6ayea-{gD-rO^^S9&TS`Ob>VZ~cSbj#!5~-<0mE*VzV&^BUPkP-*&}`x*3t'
    'a5w77oisS*3~`<BxP{rY;fsVf?LG;xYiIX;FV~{r#nyZAUhuwlWfnEPW+cw)wSv$q&G(7PbbkEpQ=%!OTzq&GVcNyap>mYb<qS+{<o0UCSnaQk'
    'UKu*~iMN`)_JJaM1vt*WOe_u0xf^Wm@1$KLUA!qd$zh0om&?KBj8fR)b-BF>!jgzKkkmajMZ>MwhAe+R+G^A}e=YLQIc~i@6K*e>x2D-X7xAO9'
    'q=o>0DjRL6ek3<r_0VzGXk`$~tD4?>E%n4k{S8o%2Y%?qXvB?bgC*9!-C1g};lSm4EdA=zZ%RD?5c+~oqq|{eNM&()eG#eZ!+Q6+NaR`X->p73'
    '%DF+OJ9xWJtNGooDqmH>nr`h8w}9x||G@NWdS#YRlLNu$y-SL`2yCgSld)0SqStnpO8vO35T7aeVuQXJB`ZK+w(e(MYc_|2leZ3c3x2w<A6Lzn'
    'lYaH<`Z(TCxgF>FJ$du{WVdy`AeY5ny9}qt53hHo#=RXcbs^H}Ds#`acL7{2V2b>yx5sH#3)a``eHuS&l`D&XvQ>L82c4YS1Ig-SJhUbZw41-?'
    '(=|sd`C!}RogYEUkIl?y>IyCE;|eLb+Mvy0?N&qmUHO=0%Y#jBMa;a78s|c+koC3yh%n$wnn87KmdDIym|t{VzUmB+oSIdi&tH6Few^};O#FMo'
    '`W&F2es@z%Cg_cuR*Sl0BRlUFoWElu9gF~WMPb=9Cj&id)!6K>WA<t3l8v!zuGa@1>~>agBOKlT0t+LC=jR+ZSZhi>A)+AWTmCezKAUTz^M6=-'
    '4=%-#W?S^H96rp#Jl2sn2P?dH685bJq#Q^f1d;#=_uFq!J*K<bOwW0DdR7&s3^J7&5j*xyWl_uKAW~Qbz20>^Xt_ci*$&pD(*3zqA7X^~h@OR6'
    'O>{sQIGq_vJ#t(mEKJftD7}uM>EQW7f-sn;#V&jDE7?k@rC!5_ZE@lVvvZQVdA1q}Urz4m)UOUtq8jkieA$;*X*He$Ay-wGrQ;|+Xb>Yg#=19r'
    'Sz?>+aGyEGHjCUkUzO_B7B!tT%Tw&Y`IXCM=gH%Z`s&C8Gg}$Nsht>ANO2m?PRjVu2tC_m!OT5h-eYgpV=XB*DwRp|6wC1AmGH14nQ1SIJ)$@l'
    'jEP%%I<r={ZDEc%*TpDBOLKdej;GO<*o%*9#o5Q(g+~ny<7b|$SCh-yt6S*ZiDVEj9?6DqJkFQfuH;ZpJ#P3SZ_B3MCbr8Po*7Y6yj3S^14*d9'
    '*jKR|mwMO1F^Fq3cXIFcqc%i~Uh?OAG8Xcsbx+xft?q5Nna-+J_Ao04*k)oi$Ln*=66!&;g!!SaJl^%Kx)^Q5tVb+s*0scv5_mrMx;VL}#^j}r'
    '86EdV6FySznBAL?O|jzk!Y82EO-2o>?JXp)cb;~a^6ZfeDKXoTo!Q_-kDqxpo1x-1*PY*!3I0K4D|J$=Ja5b5@jQ4biRjtF%MYz^?zK~!9nltY'
    'W~k9iN2i%YoDFGZ6R$0#)4;$MGxAc1DjhM#ty+(&*9i3*H;f^~UF=bx=Q8zkAz5A%bK$Y5C*A0-vxz)$qZaKSugN~orm*y|x8HUB^Es#P@&$`-'
    'J%h@qI^8olejBd_uZs7qUlZq9)em3W*z33~bK5#{m%2VVYe58F@V&N*D`Lf1u4WX@-RP2*?emFgxn9mNBNkUu^-24Z-lQ?MjLNO(L&)!+7bY0g'
    '7v-7Rr%uAN5(Djr($XySGBmSU!D5pFcWbX-N^O%HOno^=)gEj;6-rtw!c2BHmv*Qh?r-kvYW;RZX>EEq;ziR4g+t8;V0_WsahiGC>$~aGpBg4@'
    '8CLdW`5i7eB6%wZ4QF4B;B#}k8&o6Qf}I^wM|^U@k^yZskNc*%3y9m^7hd&<V{+&ei&RS8WVClC_t!&1KcAA7%+UeXpbzval@7Panq=L=FE_ck'
    'Uyax#R<K}^?>%bQ)96%SugjHIiEm$@1M$?m*tO+Uor~QTeY}U|e*ah*<aX^`G>@Gesu-l1l-u`tD;bKM8(i2}929J6w;RC{%U?;ajdZToCWQQM'
    'le=*Kp&odKi&Zy!dO2lmBje)+vKIaHetXJ0IYx9`@QYm>c|j(*J2Tf*C4688vvjjw?Ms(-&8Lu^ryR3b4(9}_7afsj&A2vaB{QlHJbR5nEbLFm'
    '`KCdJCfyVtR)`eiEj=bvJU){9xJ+yJ1u-rXwR69~$o{&sVlrEH;P)qUd5Go0RC%&a*eK~<UXN+NOUSQejBQUx*vk-nvADen`mk(`7aY|Wvg!5K'
    'O04d7;($|Z2$T0)d&MW4e#Le-)n<2;4%%*(TwjlsqL-l`*DJ9z4~r4$h*Y7=t-UCfi_}|AvSBI(Z6KT)bzJJO7vt<Lp7Rk_F!6jU8RM&jW69io'
    'z^w*rt#l}CGoE<IW=E#aE<4nY*a>xc{OT=2G<ua4eYxcF*C8h7oDGq$-qqu{0tK-dQ<2yaGn3_d?$l#UBe|)Wt&4QbIO;S$X;#ASbCD~{ueMD+'
    'vi@NHm>c-1O5Cv7GMyqz?$}ChX6@5_T`0a<wS2ZqB_*`jXM`=cOc+`<BX$Wfk%>3rG<%)yQ<(?2ukMa&lTN$VYj)cwze&<edEU(phE33Q-A+cb'
    'r%RE{(@RoHoEk}us7)f8w(zOtBD^-bnOuB3%?!QF{4}0zchP=qxQso8P~*_vwj^t%%=qM(U<T5Kb_@|^L-o-_U)@i3r=LnZT{@#8s-o?em78U4'
    '`_@i+v@G`#ux+&8de%%??w4Nn)%S0syDT3pvmi>(?(u+ja$YFigRY;J>HPZQpi#Hf>dG~26}t50rAAe-$kTWps@Js2iYpXzI_u4>!p7FMu@O6t'
    'EksmT6FN5&(})SBBU@DL<~Vbaw4CrZW!;kZImgl~z1n%@PpA2Onk6Oz%?{~_ki=Q15ZaYFL)**zL7IixqCsi7S&KML1u8GtwF?`X*J{UMHvY2K'
    'lvK&+p%sZ?&C`^cMdN4nk{GE=+3SR(x*r=G*0wVg!ik0#B(ekCs+Z=p)zLjh;xWPvCKQ)GqU^EiFCW*NlZkFrXN_VL_g-4}<QX1fB(_s1Ng1P*'
    'wV(Ti-I!{N>noIJbLY4+#8>AW-(ep0P<wmXbw=E!w>*^lUa}SIpKikR>?PdQ?R7`0-Br*|Z${|OV0drd=}70vwZ{a;dyb7^)$%=<XPia6JAEaU'
    'Cz;Kd@%6GdYaWgC=|!7HX6`1X(jw_yPK0?)FSLVDb`EtzEcC81?yA=-miin7<-XGF#VTY)h`Fip$&cYuqhL;p5XtZPBnrZY6jO!F9NAhuWTMq^'
    '-><HpMd#8owx`bMI8L$2<Hp&anxh#<*OO;q(znQBvWb(6Rem^Rajz@;!&TcD-XjsdCP-8AB3w}SG(MFx#){1imh1e`J2fN6WAiv)v>SP8rw9b='
    'H_qL{)avgBF`dNH=hUEl^((dHlkK;6LRWRecvn5zdQ4|Ss5{S}gL7h;Iwiw`uP2w*MOAN?Y&uLGs;6FwivvT6A7i%+quf?x)$rnLvTWIdQ9myl'
    'Qg>6ky$0;&(0jgSvz#><zKl_Znl{cuNx;e6>g<Ne>D1_$%Slq3?bJg3Ue6@!%5q&9Vdq!KSn)-4!&3K38Y6ez(%edL>3neqa5za>OQz)SuKhz3'
    'UDPX!oUZfg5QEX(9e0hYC;TnrzC0#-ziwK`y=Hx{;+&mckW$S%x}S$T_SRUZgjs>=#n9N|Z7i|8PkT>}x?w~-Vph&O#Q664(h0KVq7<Ip1b^;#'
    'XF)ktd&$y+JJQA2+zwa0H5Y7!qZbVC*ej@8RVkR#hdi-8If-+bd2Nri5&eKdn_qS3v#^jg3j?xk)s01Z9Z8mZZfemjv3{k}6}9>MPr~*!<1pAd'
    'gX?3v2+LuqX&TSHOi0ISbKkf-t5kIy5}lGH-Pyu%+c#SVTc=I=?k{W0JJf)!QX-e9#VHa?%zL-ek}41BhAy9PsRES3R=MAmPkwk;%bqUlm)M)D'
    '4h2#p*Up_w`Q725=SV9n?pCpR*?irSVKdX*_|&?~_pE2r7dA0hzWP!$e<>u%9L{f+ZmHj#rcT0QbJ@~CtV}vXS;lO|6Xws!I<%ATCn4fkp_tM0'
    'C2?!e2W1zgruwBFROexzxP<LZM9fx;$kfQ-l_pQqXhjNL^QFCVM44n{Qp3yvacx`CTlVQEdu(_fdeXwqp0+ZR@n$|KOcLm}X<QS-PHeQk*OIT>'
    'g(26$XnvSRWYN{QMjWwSQ%P2H{6Ksp*Ez9H4LQ79V|vMBvoywT`*n7E8Y9xKg$3~%o*s&n7avmf7&j*CUG6^W$D5l<MO4h`(3!e5xluzTR;Rk?'
    'I=$VCZs$;miic20Tn(g>+AdxSL}*fd7RQgHIL;FVrq+DPO+9Rq#snB3$4y)!ICNgBKk@Jp7e{ttJf=}{L9uQ!kMD0=o0yy$DW<&Cj7v3R+~Xx%'
    'qX=e-6^26A!4fTNk+~jsuXV9ek94q<&vuDyswR)5Y7<Wu&n=tOj-^oD9pt7&Dv4HiGe+gYaYJ1Pr3<!UlPt;wxDb|CiD_F8hi+WIeLTDEQ17wE'
    'mRL<v=)5kjquXc`o#}a<bluo4Yi@9U<jhlH{z;S@R9RqxTd%U6OaxqQRMPqIlgVEXg=Pb-Q<`@>C5+VdmTwcuM5==w%c<}(Q^6K)<kBA`n{GAc'
    '8+qG9<Ym6DyTfc_5IJ-HuIkp(k<cpVJcx!{Pc?ij{#dZGSUE4xU8QjkVHdLQg!ptJyk2G7lGn<&s8c-6Y(&b>Nypf+HaJJeqv93Y9=oMzsh;&?'
    '+s^S&9^jeWZP`iJ)r5lQ?(%6=>7YaxKjC&W<D~BR#Yjx|UirXYfkKBe%J@)h#%Ug%DHdDKT`G<jstYVqc-4caf;*w!qWU~{+-bBCd6WuSx3#>D'
    'L-$A(OZLL@BvP4(VQ02F;bd^I#mG@AWlrnc<yKt#J6cl~wfmkD(kIR`H=*Zi#qjiNaaU`dRJvq1Y|<l{Bbjyur>aPy{VLXO#boptvK;xua&*>B'
    '?lqI2E?mEG%cjQ}=dkJt!m%|RF0A#m6~dfMh)rgSGDgSuu~#WB%Ei#qZ^%-57eA!;r|q)(8a>aBG_Hz6tXYjuGn1WKk|wv=T8TfCyXdvHAxcsx'
    'ISWUk{=9348G90$v%-bEPom{ymC>rUQV_)Iq;vC#$AFAuRdVU+0WsLB<yTlKobUVfd^;CT+S>QKtqrX*2aDOvW7Cc)&yHKJTU_2+ow+0qQcP?@'
    'Kk4>VK1HslM0uAu?@rbFp6k_<r9^>gTDOeeT=YVbg@uLaT*Y3YL7Z6Fa<=xMZzx%d#HZJ5+}l*D$1`oC^z4)=6eFuFK2NVQjq6UHjqgS<D@42H'
    'Kpj60E-oj0qbknSY;Chx(|yz>k`k7Vj%)NRZJ#F0#PxSh8mqPl{gA^YB+5qHOP}Hs%%d#RujeA0wvs(VC~RO2ufxLjQeUk*^~p1_PJ}jfA>Q9E'
    'nP$5bo+K()HE-?09r1Oa$BVs^UthAdZOJ{QvJ*9aZ|1_88A%%J-K(5!_ftZ0Vmq0X+0(M7tyIlRWB9z8`*k0+ys9`JKE}smP1jmdbl@4-NO&>i'
    'qqt9d3aJg*a+uu~BSJ$NW|~wv{>&-5dl$Ro4Nv2>VwK7d5BRVqAsd+GK`B*3IaCgn170MO$7kBvw+q7{-6wNy%3t3jtzJ1DsYFKQM>Wc=oVheF'
    'bDc(SvCNswu7TR=n{ULWH757E)k!0(N3-pk7L8pL{m_h(o%!~X6DO5n;53^}&~j9`Ok}SKy2rLyEj<zAxo6_hyO!Ak$66NFO%?Igy(f9g{n6P>'
    'Uy`?1Px!6g>)laZtfHwmh=-njwPM)oSrfYu&g<MM%~Zd~y$Zw2W(M#$LYOsZ;LrP|e^d1F;5^F-eSXIH=cF{LTaJVum%DNU(+_yMx*wghVvO|l'
    'yV2-+Ma$c$P4CbP_P1hKY>b-iY172dcQ(MsvbC{#&0OhrexF>Vg&8x)`<*SrmFRO9`CM<q?P52>%*}Nv+NOftVkbM^g#bKg<6eZ}`D7UgXS_ct'
    'M=1L~IiKBHI7k`CP_ts!ceA~*xvcuWIMj+wqjT|_rkdwWb7SkYxX0>p@L=d1X&5&xqBHCQMcGNFJ-)3jo7f=A6PF2@(JNwDX(+j9G0-e@HKhS4'
    ';(B><%=8M+Lq(g%cv)SQ2;0f?lS-0aHrbtUa&)vKom!2sd3j^fw>9B}YMGjHK0o7P(v0>7l@OOM5#ik{U96gNDwGmRGiRL*D(=Kf1*SKxBvQd?'
    '<?CxLK6b;=&Tb~e&Ukq{y%KSG+^?(*fsc=s<D&eaH>#)<Tl%BY5a$E*5IY51=(EH4A<>O(jeIn1UNiW5an0B6s{mhB%)*!n&y{ECQkkK?CVO`+'
    'u&$>?RRJ!uoHoYftXNqn^V7Dr@rIpI0`Dbi_iJ~9X{k-_rj~Nm6t`f{+%bghU*%(Qj^S9f7_aJ)=Pg}Lj3!LU8^tr{Af@bE*YQr4E16O1kWZIN'
    'c+!lJBFd4uT2botEr|*$o%=&AdJAgo?O&2oE}FM7A59-N52kvXIy9Yq#<6_T+J}ryf)1ZE%D(wH&&On0rM!Ivm#xZbo{s3n*RU8vy%UZLbl_ZE'
    'J~4>Jx#^kYE1RZ|^vE!vi|@ZJAqecK++Iss?kVpVOLMj8Z0j!~cWj{fxRkolk$@fKO}?xri<(kuOp->ZG%t$m-qZW-s3WnxzG}!Q;1A_pcE93t'
    '6Q(D7w#w~aq@Yug(dK^LX`4p;VPDTmG9t$&>;CMF7$Mi|`qc?j_af2OeQffl$viM`>+2|2(%qaGZm*>47<cw#F5J!vfXQc~N~mLJvdGRCRIyo9'
    '?d?LI84GW&2L(z9bt&b@7HF;BC|@Gy_F>@d66<Vb7$X+3F86wAAzF+w#672{n2Io)CTbDOM&@KZ&zH3>Zm#DX6#42SRn2o^i?fw&lw+d3`E4Z^'
    '2LWTm3u)C9TFJw#@>ndB69?nNaz8X~O&@Hr-zP@73csKd^~~+WCd0!{a(0radbIfv6Zc^+mPsd@{c+;5@feZ2tp?A2amkufae*%f!(5eWy%OUP'
    'y{g2EW4kXD{Cd`NdQ5)ZEFPcn+e4noVLxk^Z03|Ai&}vV6s}VtcY~9qQzIf%*>pr9)^U61-ZC|L#`(e{v3pdCQoVMJT9s7bxOOJ0Qith`Xk4o6'
    'IG1TApK%UrM!1W3zTAuPG@hY^8J(|5+cc9x<4ROmYx`{{Z%A0M0j=OoM8D(WMy)6H&D@gclSe7`GFCVd3T8+Z6U~xMU~44hGh^A|7RwjO9ir`N'
    'wU#->h-`V5Y??|ObF;PKcGo&}yww5QVnmtU9t4$8<CWa=o~)!?v(cJR<GYqVRnzM9IaMpWaKGM;l^=eCnmw6|n`4rd0`gBKb2RG^-7&FA5>rOx'
    '&1*kE>zh(}CRZAFOy_DNv~7rZRHT>rgCQD`%PUcm#f!3}Pqk-`RIl6G_{#3s%Wg1kALA)`SIxKYlbFQ4dUTK4ZjJC@6!Qw}Y{Lnq+uh-j%T*8I'
    'DjF=yx2Ji@%%YKUipz4-dM-C?h7$Kp66!>Eo%M<tugI&7La~#N$hWbO+C@iXL&J_{PIk(<O~me&>Af9a-jZ1{pSk<d-aZ%7ixaKWh~VdzXROPY'
    'z1QJV&({3fpYM8()5%{J8lUqjrOc?-s97mFeetbxVPP7hGrAJOX}sMm7KQE3Xft%xsVT9u=$nULF22Q)zDU=7zr7;Ee65!88kKlB6{lt$G`iYm'
    '1w6YoPgbiIdm?Fl3{sd>zF*zpaa(A{XWi8zX!i1s(t2FkG#<(1E2$<qJ6ptUcBrwpS2QJw<T;xNzid5~TBmYbTI|FhdJCJ4!!NmtS|*5HE4Mfl'
    'FaGASuhJ*7wVP0@!Fo<6%&GKDM_mT7o*ll1bU87f;Dg4g>>ihs%d5sUgmI&^Z_t_BV|I(?a<4(sbPpSO@r({?V(k_8m-t#+GV=zNauZ2fdR>Uc'
    'vKpS|VzpUG>OQr4hqxER#A#mVt+023DZQ@8yK#7h>gi>o&~41!wqZ)gdSJfPV;0%vc~<kNsdqeZ%u#){34zN~uNxN*my+W|fr}b?M~!2tBZr1#'
    'Nz|<BBmN+P-OnolfrTrw`@+us7rD8York4`iS=Z7Uv>I+!OT$JfHPm#)>1O|bAIxvLOm5S=UypAj?V=tIWDs}P0EdJD*c*~d(!hJqeiUS%I=Gq'
    't@3EytC<SpH`wD7KUGzVrjvsZwVKOGiDa2=KIAc5MqV1N8#}wT?y)>=b)J+qoi>S5%<&d@CRM5F6}p<%Z?}k0@f0n;@kWcBA57U~DpngUEhlN+'
    'D$+5EVF{eSFwfQHiiBHi)5m3A<!Yx&{JgCsH%;6v3JI#T_pBV<pRf9&n#{Md)6#gVUgwk*a#{1pI>RM3zjVx9Tey<9lb=bO5pT*RFM2ljatiHd'
    'zU)h6(d}-Cc|#xq@=5JoV%Zyn=GS&v-cDng)_RGKEk?o%ozUd+sOA>@p;1mO^-X<syC;^oOwC&eb5efKuo?V*g5r8BkB#o_${=^DTm!w@y{%g$'
    'F}W7B{G+<27CfG7N0?eri{10ZUMJb)m9$5zm-aRi5es%&=(O;<(u-_pqLpCCUaCHlsc=p{u7$&dOvk#DM~}X6x$9$5UY+*~FVPu0%Se`uCQsXT'
    'lAPUo9$BV}(eQkE?-%FJsSvZnR;apt9J~T2N_};EdE{dKB=$59<!Wo9@=O*BKy-3dZR(uyjGH|^6W5|ogwJ^QhAM+Zo=wN<G?ksYdSx>$D38W)'
    '8(|5P@6028zTni&`$iuf=PP$LJ&3Lv4{y9EO?%hUxv-_GQ#s((rxEu%`9VB0eeO*rrVL{OQH$@(kx=<S?W6fCO~?Ds*sMPCXOx3t1UD$tSwA^;'
    'm&@6Fy>RMu$*Ae1bB}X$x8K24{g~eBE%fNm%rH4z#>QmCu0-<Pwy78Wh(u4!q2w_bF`{0@TfLEYu12Tj-}?Jone|%BU=KQ0+=cDJIlHyfS*)4C'
    'k7(Dn<C=^g%gSchyHm$zbE=SfKyPMRF^!Vp+@;%J4)vsk#kqq&#SDUY($NEBOi6Nou1>t&rD^8p_2R49y(TYCw~OY+1vBTf&4wJFw-YWraQ2z!'
    'p=(Z7^i1|c&4x>2vBqvLHaix_B-g3%O)BR-yYXcF7{40})!Gv6FA_1tH>h`M78w81KJkjZIFG`JpYW}?)>4nE+}77ZKG815SM_uDHe;m4Rd>5a'
    'dOhG1!{%AbVT)#XoGVN=;asjcW>$k;RUSQ-T$|zDs$%Z9sQtL>m($d2Y@M?~QHh4!*uBX1=)mcCy}Q$&WOmK0<b-yv5_#Dezap}1RI}4+Y1GQA'
    'r`Xlst+je3ORhrYJDX9M`ivLT<J3kc=ACZ3Im}Iz0yb%K2Yc)s%ME-l?Mk~)0c~WSJ@m!gIAJ|D*Cp?m4A!efcw!p4)N<lB8!>$$=WC|0tv!YH'
    'K&}F8w3F#;wi%C9q^)sJ_mFxZTHHQ-?0MsCAw1IATEA95q#ETzC|a##leb{rwyJq1hEF1eNY|zljr1_8yht8PBvf_ZDQ+%{n7L2Rxm=i@ORwkX'
    '(e&9#P<0&9oKUk^X#X<o(|)fs%=1v_K18G>9(qUHrX$C8x;<^#_JkKXrddzegC;LU&p?Svy%gF#E1|}bT~#V0+hjJ4MH={Y{5<vCUMaGlvd5j^'
    '7qziDX;+esCYHywN^6i>IDs-vh|zT+W2Pswc18|zOr(6r0(Uz>%_v>Ctd7*Y-@7F5d*w*cL?(`l;U(ZhD>Mmlx%<;b%(O+0GSQ-R>emRF(N;A+'
    'Dn(~q2$6YpUmdZl)nbJDw{CJ$8I#@%2Td2HXTmLLK4pdRwzL}SpRiK%(#y|CAvNs~TYK*q`5U%g5}Ko~q(vLP4=wuHJjiYT+|L~1?Npw7-t*kj'
    'FQv6kB^>DM$f^(swGuZbSC+7A(%#EbTwz~{?EBH(>U;~C0w*w2@0Fdlj5}H}vCZ|E$Wgko?M8P`{J56p*IY)J7FjR6Jmd&LuiQIpC&n$sW^;T9'
    'YMEKbyQ!0Id*f7lSIe;YSNU+QIKxiWm8^cMY46(iHEKSC9Cb&PWquwVEUM&T8|l_Mm6zP!^yFr3Guii|8A~`c?yF2`y{+Bj>T<L<hP#GdeNLQ1'
    '|1=msxPsy=Qsrgzx?AQ**3ES$V(a-b<zAsNHEI_sW>%u46g};?PD&dTqpiMUXQ#YY7jxyHcQI@%bxmX!zN8;trMxl0OMG^QtJo?f3Q=x;wpSCD'
    'QYNEQ<C?Ub){KokH=1FnQXJDw$y*MIN=HcRrkIuT>Q!t+Cw$KDqKwIDT%-S}w#0qNS<cLC=(2XD(vb}hI{8(JDW5N5S+~m9F)_I1HgSPETS~6D'
    'tDD<JC|Es03xE0C&g^}nDyXy=&TF<YRYt0kyLNFtEpvK%xCmDjJGyW8&dh!0M0AN0yZhqN*sc;>{w}uD*Rv`M^g4)Xo!oSf&?JJNo{ODhjm9I9'
    ';VM0^zLy0yBbKaeH8Wls(M`Csk?-s7{A2>;atlhI?X;@qPjjtN6xH<5*?eued^>y`VVc|Rotmq1^wq2L;gPoRyyz>0M&m8BF5v5HFS!wNyKBUn'
    'H2C?<l1_LnXx=X~)~8p4?8deCr$UjN<Sy&Tu}P<r`OM-zY0DX=kh`m(318#IrFF@l>`eGnY4^MS{fLv#VhxSD@hNMj__VmuQZxJ1j~dvM4~Ij9'
    'sa}ksewle_zi;d5vrJ`zB(^Lv`|c)|NL*Xv3%RwD6uxil5^=TaRsHF1$4hu=v+wJA3TGsry)5lWa_diyR`GrtWA$$CdAY12M}D4aYzuNZE_zB1'
    'gc?#~sbpc*EUl~L@Tyd{xu`g{ca-O<%<=4SySh-b<e@%tPV+3^*b@GtZoX2N?rMrrvsrf$X=>a&%@R><C1<Iia#Vd(*-h8_^g4{|+t`vZ51D}T'
    'tw)5rdJ0n*h-upEp6N_-)LBQi$~3<4XX)?>@5PrhC$Em&Yv$;LC-G@5(-{>Xxe79uENx&Xe~78IDP!$28!U6}SEC(z;i{`s&cJ%3D;~_7(Xkyl'
    'iWk9J`}^?lsg!!la<RfUOKMW`s9YJb);4K+wfHD@X?6BYU_0wBHci`&bB@j*8-7i%rCPrGNF5HCX0v+qDNgqLi-tD_E9`M`le=^oD~$`y7IiB}'
    'xwX_*3R1jiILdvwIV_~hii)QU-t6Gk=wPIRrI6n9mPd#0%@M7zNvj<`6aFjovNR_=J}KCv5hW_U(+g|#`TfY-QmwmeINg-*waxHwk{rr%=D^p|'
    'TDb1NCS~z>RquFk+yezGv=4_xLoHy35SA_){dKJ}=c3WxG85Yp1!rFu){B=Ywv)tB+$UCB+Plvy#A>MSD&5P~ZL#7aUN-zuP??;j$pfZmGvf%5'
    'c<U63VJ$HT*A~O;xVxHDlEQfs(=OJkf)%PqT$Y?v3W`tg*(#o`lu~>ubm=gsT{pHYk%`Q+IBoC)wi7c>@nM#;3+fDTJ9JJfiMpmvYiVhEjq9v6'
    'I_{Q9MX4ko_rpz2arXA5<wCKnk&*LeGTKRxi?~utF=cnwmR$ifO{8qp)xPYHHlf`j+|5wS5JT<yDB+IuRWBn`otKu{7a9+NB-{0JchXpTj~ZKI'
    'r?d$GD9XL<srMY5YrAnMaVx|ZUaBK_i^-&u;H>fblvz+h`a)L=t-z6*{Z>;}H8Ha-+TmDG7-;=iHALPf(Rm}A>W6cWak5K?mZ9!ie;&;n)vfr1'
    'l)o3d!{NwS6T=uj6c;7iZ|LidGY+AqW^$2bV@R{-iLU0kIq@pr#Jb_-Qz$a9Cbn}sn$yPxUuLT;-kwa0l}kQmUg<(o>old{X=QveoCvhTgsvM_'
    '9<n4{*dNZg&Fz<0DIFhPg+8~(^TTmXFk9X@uN$OIwYCk0)!Gqf(5d^app!TqThHsfWMHMlb)YQTljr1+KWXKA`t&*`PKn&+*p0mW=hVAts#I{Y'
    'o^)dZZHuL%ok*JME&J1sl)9~VPVMA(N~+~|FAK+!Vv$<1AB!AnL0@ri{w|a2j?Z<1RT}*~V+{t>m@p>WS~J7SgLCp_cACWSTGsk4OrBBM5X!|8'
    'li48X$HU#zR$`?~iR-q4JiFOU5A`u9x_+``7JBP5wcAFS>@0p^;|n5t2$Jc$G>G4ed(U0AT6e3J6{9hw{>rt_Ln7Ne?in}8#)5EVD{jwX+}>0<'
    'r4y8Ean;CIHe{$PH1E!SD@~5nD1UGWuNLK!-r?qxsf1?aYDqQ=GO~V5ThlSAlATE`s%9hY;`p#xD&ye+?MeG6)2F>6){jR`J!O~k+AhlT)oUS_'
    'Yp)K~e&sZcAn(SeTE$Ja*sWPrdc579@9SbZJ($Kl%AA$dYH-!b=612ln6i;St&6X?c$Q~jTPQgbO&8H{ZLEtE|Lje;O=oo&PS|jfke^eryO}U0'
    'dA_!~y_Jjc_EW?QBmNp5?)Mw6xzMxzZgXF0v!E8)^u4hk$}9)gI4Lh*E%r9Q59-)eXp~~Jwj>F*QEOEL*+i#hwpYz!kLq*ERyTc3sU3P{cfy}L'
    '`KBgRdi+e)QvLBGJKWqCLZp}2j@t89L&YOxv9rAygAqTNZJRSTdoeqe2#r1b9=6KW^YNv+3P(J8JKJ32p67?!XRLCGRItcI81^n%mQGZ{%UXOm'
    '*|qYa^sYY1@Ye{_H&5sW|H7+{XYSIark$CdbKUdVObBh88dclTCf0Q7r*KiSkrfnX?qt1lxfy|9v0k@$;%iS&kK|GN+#E?pDQ4l~VEu}iVx=X!'
    'r)^-7oxB<iW30R}>j+olL$%S^G*XX;<!Wla{67A>J7-^ui&ZA2R=rlpmyzn-QUk2mFvh5w%#tEszqdhx_1c-yZ7XTPO1viu>(g3%Ui_PjrF(X>'
    'KuzvcaBOXevm`~O(vT}2S-HQE;xcu(HLEy*=*@m`Tlvk(hREW_@lcA4rCq$0zb2x}2rn(ir3IT8Ofn`$6=B(^mv(KpJqtytezI|&5WDcoxDI0*'
    'w#Tm5$}69#huLw4>jn$@KAG%8%^V?zUd?QcQ8?Dd34badwx`7E60V)qTmKry{q0CzOhYqCFS#X!%iyzetAD)@@RB*oK02X}7@~|3p-d7|w7LUm'
    'km)3U<p+tw94qWk#ZpBx#pz5N*4R1<CD@*uO>#nD4fkXvc+pZaKdeR9mkB)$U1JybupEO#PWKYody5Y-#9bv&x!e>(gC4(=+hIMQ5ZP;}UYIvV'
    'QoA)TFv)yKE{2Qt$}Ao`kMcPmD=BVCj}3d7o^lA%{n3saREG2_*ep;kff~eqFg_KsuVIm;H*|~0T`mVabQL)g%~EPEM>+;gjI2J&o;&h9GvNYz'
    'P^d;#CCP{-LcJx%Lw_GrH;;Z`H3tP^&<i)+u(1+q5x?@Fhjc{DH%Ibrqlc4~Jma!cRS9kj)|9rxv9Nbz5;|(G6?rhsm`t6+b9Egs>-CUeVwvVW'
    '(%$E{VyI}&rjM4Kb&FivJ<V64u0M?)o^qtuqI(0nM5SZLU|VXOt{%0rXSruSeZ)HIbA6NMy-qb>rwjgOIGi<m;f`M(+*3}5YuCn#7dp3}rn_Vm'
    'LFmv7U4C>uq^!?L8LE0QhRyYjwrfnUr=z15+=#$77lZXK;>V)h%mb6oW{5)%T1dycix=B$sqy~8T^sjhi;G91hYf9>X8WwLcvbQKVi(BS5H4JT'
    'zO5>vY!zTSi-NCJ*@Kk3wzW#KJl&r*?Mw94aCc`;EBcM=&NJA$roW<(vm;D*{E{g({C;x6*h{8M#w}wR<4@e2b*uP^jWp3qQJnFfyxaAxobCnH'
    'Myq9#`*u4Er6nk*r;SyElW(|5c2d!BMnT*0?Wt>LR}AXu+><a4Nn=rQMO%K&51W)kM;bAK6GNe(8(vh8oEy(I?qcE543356)mY|0LN(*%=Y6#5'
    'RyNz{EWh#f+}_L<(~*AFyW)LGZCyIWl0Z+{+KmZI#A)MSYloLs#CqbBxX;tg$+P3mLVRM^uvoQ9aMkQ<#cuPRT)%W5Wx8h@<4yUrBf{78Mec>#'
    'rTxJQk)=UU@dA5W9Fb+9O#7`>N!2@8y=C8Psa3z<D_eKk*%W7mq;Ra(xRB9XO}j20IhCSzCmiRpi`_I&aVBEB`zLO8ZuWW<D6b4o)l9wAxE7X!'
    'XDnW-<T`9^v1gmE>Uo5cj1leS>KT_?*Os(fbh~*`$_<syC{mrUT6B9qFCUoEnnoWYsm^894tDscJm_W14WoPS+7G%&NVZ^2;*ajW3pz#FE2XpB'
    '+f<L#`gtgZPDG{4#o`z@9%0VH94?1JY%#>gDT16^qfoq@n#7LV-H^ts3SGx0P9@&ZZlObCTx0{tluG6(vQbo?k8tyaF^LpO)&BGRfBx$~jzz4D'
    '!$muIwiEp4fBx(L{g0qt&_U7E|E?GxA8&;mLvu&k#c&NzQ$LQx!TbKQs`{Fv7_R1i*HU-Tar=vRwzWXg9P9fx_GR<^$y%2m^f?H;t$q087p{KR'
    '@kmq7jtjT`a})7wS;z^#yZ&(=@aJ#yY{dhMzpn2$wqtl(O8{CExQ6@R!U0}x9As5A@5`ryRekh6Q~2|@l#ETkXMc6z@P}4kJLBh8-#g<wlkZmj'
    'JByFi{dw~byz`ySKy!54vEGYj>tB3UK^_u4=d5^V=T~q2?3wQjrd#AS-S4jd{0*O+Rzj|!RK))-q5X$b#lVv7y(`qUgXW-p8M)t?mTkxo$1@I_'
    'il!JA+V{?utU0b{mke-8@W+pz-}aq1{%rW`lqvLxD%$D%KDYU?O24!mp0(e!6ro=2e#`REcT~;M)VI@rZ8$#If17rU!|uzg?<aTA4S(Qh@D&}@'
    'f$e(ms_MUgJMx{A-`Rf-$Um?Du=DSO@6VP2+8YPeu`R8<)s&s)d^Qk`_jLaB`T#jFv90z4?||WX|B;Rj+Z((y)Bd^1z%f47M?&uI`<}jy<v%Y='
    'TkXT?g6w(@QoMI+NWoG2f!$Z$`3>uj0Qn8OkMQ^nyKh|nPxkM;6dVmALqpE@nf|p|)BO_lKWY1z#*f+z_e*4dZu^wsHOD@9UF3P1^WPA5I#T{>'
    '`cjkLFs+(!`Je<}2mbf1(2HaE-?e{17F(|v=I*^Jf5Xuy(~_fs=-Ji`0E;iD%s=DRpN3~+uR<I_NVX5gX6w0<eRe(?e{MMi_jHg7F8YySMLYh^'
    '$p1Kp?_lhY>wf^|=V3ls{oq9X4;o=U-!IiKjK5l=PgbAd<j>20zu_nA@IAEr(EurKx#AHW4(~jNIQ!W`iCf$8G}jv-Z#!^o8SeITUyv8}VY3gQ'
    'q8wl}O)cBj(LTVWzO(!mJN~!|N%`^WXUX`t*;f<(<6geE`8$4oVqzcdy}dCM^zqSQF#S&k6I($tAfXcg)K>uV4~F+O#{XgVDL<PBSOxX`L1^B!'
    '6@J=(4;bHAed+tKshtnXHzRy&Ww^@uqsjn;xIee6`U(W?8{px#_g_uxlhvoV|E9IBdG7@QJaWEbioY<qLd3k?^+VI<;du7oX8LCjUi{GHb6|hd'
    '_$7Gzzzz>E6nOK^K`j{kPZIFw0+#p4{n?bh&wy{5zv}hZOY`Q>+SS%S;Q3n)@{Qf65dWs_ODT9~#~EN;RA6F?_6y6eZtf>mf#{vp;IG_ue`)qD'
    'TLs5_PPiYx{ZpXBO&vAok0t+av^swLygGg?$x3-&|FP+(e*O|P|6N9V<%4;A;6E&&t)nj=Lh*@%e)Sgnjhp@-7cSaoWcu3jPnwGkFfDBZKiKbO'
    '_=qFn5R|^+#(%%<7g_g}QE)&OM8o%P`rGEasQS9;xVPW;fx77SgL|m&ZP)!Omi}(}oHl>Ad>`(Aw~2=49F2p!GbG1AfY?76^Mi`iU^bfjb!qy`'
    ';0N#cHsJqm04$ca;P4K*0;~8%50ZV=99sw6vW@RsCx&|l8hrcpU3^KHUl@FfzOOz=@;eWG)z(1n_A9r3)$-W|Up0O2gRdGtE!VdnX!%8XeM=NR'
    'S)64E^uIpy^1Jrt!F@;jS0CX04}Zb_AN~m4Z+t@d4@`gtL)bup{l!ea{qW9jo86CZKVEqE+oJtd%O@9q`87yk()r2nKz=s)O5cCm{-?b9+B+XD'
    'pUgg*8yY(PYOuep`hbn-8)W&~;-|y>vG)Qg^~1(bvHa!ouWsmbApg#X0R3gwv(=AEGSYOARIo^&y7@j8zFY^T>T1$=&H`5YE@Z)nSaRRw;_v19'
    ')WhHF^O^eo#;?Er!0Kn-_>`~TT(tErItmr(+Yvr>@ct?}2#S!4_Mh7RiE4ha(rx?O3!efV%B!(CSYPvP*|vAaLI3N0#zEEoQhXLNzAVH42S2#L'
    'r4?<p1)$U1|NPH?-G67V^nd>AKLm$(ohAuIC3q5(6;hGmlE$+fNywT8Ul7adGR>*HqOycW(kibJJkFCeM<9j&#eOUFjuS}J2$G`|j-_~&z!+Uo'
    'DMnEdj&US|v6M{Xgo@D$!{P)*E1FDem`dqzBM9U8f84WukHKgx2x6JTH0U445yv7-;dMqMXbh<sj79PUBkKe~P&~pZ0tb7ZRVk8H8CCoFzAtpH'
    '%Q~(gR>L`!!{I&=$!NOF@tVp~x+ZI?LU0;~7!pI6%(5)S;yNYE42FS$rgOjAJBIE_R#Rn$)+m{vNkmZ!#*l>05V)@5n6Bs;!{fAyYb=X%1a!;7'
    'P#8n&s>b3pPSL-&|NI^ZQ#pkvd6m>@MOR6dV>pb5#YUXM>71tVnhdj`bOjL%M}Q59lR6?v2mqWU*x%X1en%52voeJ^mBkf~RtO!IL*Z~-$23F{'
    'GDG2%&Tu+Ks|u&-G<b$$NJO$cq2dIiVn5vnhrVTn;x$CG96`xE$FK}yNnBB7Tt+0%Vu+v!iqXMgDotptj5JOr8Cr(0VlkG*h=1Bke-FW_42@Wt'
    'C21KU2t<w3Ws1{Tn#5QRd`>7d$Kv1+LM0dlqj-wvWlE+P0#=Y9e!3qIee()MVmhP(!dL{Z)-alfb(R$vj=%_xW;6;zn#$m?4v54#mg5jjL)dC0'
    'M&bDXW>5bkfFUv1cdluWuoTDgBum3E6fC($L2ywTr@fOD5}M$68mSa5%e=-a3<H5r|K@Xn_u}EW!sx6f>+gs{7>RK-$58|ThEB6G4WY!-B#ShL'
    'lXV`coW>wTDm<_06vHC*H=ixMKk`6^6@<0X2yh8RtO_}e5j-N10yj?)I<7(_lMw2pije>c6sa*dtbvY0Q1i_1JfDDJ7+4vF;uM9D6&}(N=MhhE'
    '@Uu*56e(*MLYxNcNh{zqjD?Y)e^_Rg2V{|v{2R|WU=$W&nE+tXaE8HDj8HHc5sJ>ja4;-MDG<FdJBs0GlG70fH~@{hjsQ1!aNa*XCwULS>J%hA'
    'K_D4d5v&-4R0YFumSx_UtZN(r=uT@S{G%BFB=(JP3gC|{L!hAFde-tDhk(Q<6~GIq7dnIxqBO`50)y$$jIJpx!@xicAp=wcq+$x>CM1-`K{_K0'
    '{r`Dh1H&VR<5dkZSJB``6j(-*P$>!u3QJKc&oc_3K7(kLR2W*-aSibrL+}a?F^I$R|MN4Sk0|GHoT6mFV-*%tMKpjBPHT)t0&HrOieW4cWsSuY'
    'je;Vh(Kyr$1pdNRm13EH|J(=$<tRu_n&%+;065-7Q`4cuQ4sL5BI__wC^Zl*v`*oO0!TqT26Y@$C_<5Oo&V=&PcVqa(L4#z{DDU@-~ojJAK;;~'
    'va+H<rUEuWts_;W^D;mgqHsllL<3mSG>wt}&GW1GoG>2dLNYvs%QVC>18b&1Nm6m1#}EsAgynRoPf)6Lh18+A0$8!KCPPANq)Ps8pMkw+3YeoR'
    '3Ma#NSRzURMgS#<#&CkfVC8t3<5(ShhcrM7OeH9QDPSo&qG8fJ_4DUw|CdnXH=o75S5c;Lj-tUaP_rPoWelUBc#sOADLkTa9qBkrz{)X*!hk68'
    'EDg+v$5owzqL1PK;(6X1czIYQSP}-p9nwYzRsr#cXbor#IFEv?Ll{p(EtH{Dk_xyOkcPz=nbkF(!T-fG!S_lkIxrSq!+-@TK&yba$Sm`QBpC`Y'
    ')O@(iA(iJyoB?Wpzvs<Uw65S#IC+Kq{pX4>7zU&Q-ml?Mm61$iP<d4jafHI+B!@%qGLTY6Ayr-GVU2+ju@H^`*ec`(h4BC7v&lCx(3m$3!wG^#'
    'I#dFlq2FK$@un!0&M{ChNgz241{i=5KzS%wTL3u>mL2B_>R&(Kd?Ph<r-D}im&mto<Ttg!f%O65M?gM#hM;hr(IMt>66baNU4b-B2V7Ob|I|;P'
    'kwV`T+#e7=9#U8brpc44LPBNW-`!x42XB%_aPPm6p-?a|0bmWP6A&5l4DgNo@pIO9^eM8cgKU7hgd>@!;m#Bi2tC0<b^>O-3nvMRgTzRHXqx5_'
    'kZMd}2_Uu%@Q`0Tt9>(MSaX)3Ib3;@Blg_^q!c8H&hi>`2#^anuOPrJ5}=XRIR&n$9N;^v0r3Cx^WJwz)4<w+_~0~RRE5WA4A=_=L`+s0&<}70'
    'QifrGf-B%!8fZQZl^^Z~rT}Qg{Qfgz7z|KVXBA+ago5~YapZJBIw(Rw2w8|)Py`C2f;<BL3>AvwNx)wU=m0QI1UK_L&z;|Hp;a2gNSOnA#R2ug'
    'fwQU{=tW3b3d;PO(2}6N6b@nt1Lnf3K(2w3!gwGC_}_hY{Z187aG>fqTE{@;aT)=HokWoEa2?hYR3_lfn^{6VqF7KOP!tis9<WYDCT0C+&%fVw'
    'T?Jai!*UQn>{U=$@bZn6Fc1%ln8H~ZVvnFHAWw{fL&Rbl051--j35z%e)}2vo2V$Xg3BZc*vPyKIv|<?+6x#34GM?kFqMSxgVcWe2y_{gc?L%s'
    'O%tGabXED6&*9%b(%$6c9Z)>zJC;&tpo9np222CB{g#;+4nab^C85e;pl4uI0w~j4>3)kbzkHVe*5fb%o`ZhhTLcuwsrU!|<5fi97zoObx(neB'
    'p(sN+g)#{WSC#=LAn<{`|MqzR7)#YvAh#GuXDB)pgRu+-@uun!`aokS3OFte|0Cip)aAF+Fi48GKmf`I$@s6&6ufg-2I)`enyMoV$3cz*@VtdI'
    'uxBU`ECKNWYYXa$gec*GtdmfFAtwN5A#h3Zch4of-Nr%?0}o+T4$uGsM5Zu+P3~P6q5eUvvj}FayvZ&Ls11@DuvLQ<=Wv~6=wF^~c$WbZ*cKoI'
    '@KP0GkJEs!12kiAcv5IULd0|E&6yQQXM{mvL^J`{2pLC&N;1DZAMs`<JfNKnwG@~>2_o~YXMj3#6cBN6iwt5%CwLe~VM!<sIs`c2BCtD!W<Wxq'
    'U!Jje;{iu%aAUeo0r8-CP)9t_ROlPv1|$zpsUY|W3J?eC3n!B})N4*AWEqf3!!hD#=QQ3?i~yiy&}2aCF-SvT11v{@YLInM>geqe?46MW1ON$o'
    'fB_|-1A~KsXb@M*ug-eBg9uYWvntrToI-~n$YtPz3}hZ7Yd|V!2D+vxOaomc>u|fO4jNVmIzYm5^29%!7y01VaNlq{9MC`oLQ)213xJPsh*3az'
    '2owf^Mxo)ZS%Rf8U|TZz-YQ{K&@USKk7rKavmjI;<P?+?UV#jTx<;uahJ$8c0cKPN<ODz^rUARfKv{t7A^}f;DzXTdfmQvRb1NS@7HJeFt31I|'
    'KuI7dap;MK*a2-!fT~k;1~jb>h=!9Y2ecQ85~vgaZwOuj`~9;oAAEq3foL+owSYeGiVpoLK;&VuI3Vo=_1?IXaRMBO17QPQ4mko94ZH}qKokGs'
    '{LCB3c(_5FhA*0|a0*QU<A6K{yaag(Oddj;1}UMkKzCJ)1tlWWZw7_&j1H5-fBy{5o1yU#YXr&Z?~Nr@=0F2MNWV200}-JD{gt7O<S`kjH36~^'
    'q7y?r!@YL{WQ_RTb3E_uCsNhk+6O8mqBxzQc|c{rGl&y~;z<T15r$zv=$Q8w1QZ;aRAm}Lw&9>aHT<8?0)1?50;T}TkSQLZ4EPd50cj&i?mdQ#'
    'y*D)#P)DFobeW<_4$^@G_fiT)DbS$*^gPl3B{}ySXOg~b(L#di@6BYAV`vKS34lN+fh^K*1_-f@2)F?5hc$iEb{ZT69D)X#!Z7Nu&o#X_XJOj9'
    '0+GhZpnh3}1KfhL_1<D8A-d3;{Q|WCa-f0<kVfo-Ez)nd5g_va-Px!QovpDd4&sR80M9|&L(Brp#Q|AC=s+MtE@4n@AQ*KX*a=|14Aomx2pV+P'
    'H_rdn`Kq^<AOzl1fH;6I-y7+gLdqD-mSbU9m4{e^8i0e#6j1trbBN{N@TURQ21W6+Gg=>8^pF_zJ7RgLkidlifEcJZko=g+tK@qNgMZf`?foQ!'
    '-~fdn95E=7!1cckuAiOr`j~*OvnsGl{atrS$a6qdxM>W+2|$d7p;#Tn4umuY*a_-gWpo924+3V$^7zlsioHt#uzM(E`g?ar!`Zhw2Pgq{4515*'
    'kAP7@aDX#F=0Rd0gp<rWw1{_@W8X~SAI_V7?4d)V!#$A{XfzDciwAlv<0=8H>0J;AxLrUxTzx;+pb1qYkOrI(#>Ig*D)jH1S$m5c1qXSi;W`i4'
    'i$PSs_mnx%Ary@?UWdSzX<mo21bD*e5P-0F+FL17pzQ(r{>8bscjZwbED=CHNM#@o@4X?A#R%L2MViG`@VJUIFqRHUMM5wuiY9{u!D$BWfLDKV'
    'cJ4!WVDB5!0QrF0@$bzog(F}c-rHRSWItjRU4{Qh&<HR(3+3hw0B=FgAx;0?^LOw3r=dT{aBvF;`2uW_BtRpPK*2CtgMtF_rU747pc(+c5Ui%*'
    'xWa;71qKC#@3+qIy)%Y~N)PEw(<ICt7#}EU3KSU#D#%CxE?5_kn6N|~qFIJh2_Ap~<Qa`1*m3!H&H=u6Y-kGUGL&Qts2l_0lL3YWu|PrYspR|l'
    '9$Y0=fD)3$fjjX$h2C-)N*U;aZ+!BTvxFZHv=kr{G>J(4LwJH>0R~Kf9)n^Dxd-Kh1r5c&HI>5tpW4psN|W1$!nrsC?jXYfw=9&qzgz7W9qC_2'
    '8b4UJHR`S^61WSNqX^l+GG!zZD#-zVJCFEuVzJ(M<<iQW)5r-wk!K}jfT=PW5L2jv<s2BcQ`I%zBLu!4G)gaK8g(HEA*2lWUz7Tj2}H**Y?pK}'
    'nD=DN=E%K|Lr`Fw20W7-9`l@k`2LHzNIhxu@h}vwtOPZ4bHZr?%jodTTV?<eUc(QOP1%s5@t%y>jiuad_T_A)o>bDz*XBcrq#h0ueFnWWOWf4*'
    'Au8~R5-2{9F_WNQgOh9(6rEqsXFlR=XSD^7O?*3oGGQt`xf5WZHL$~{5N(OH!u4SeZbi))f50b?`sIwL<kD_~0P-?Z!%cF*7rM5`zBi}_iGV@~'
    'Sa&-acT@1R7=xnc`uV9szL^vKO?u|jtf{DfqUyK=XbcfKN$jd?;81{{e)pWQgWsGH#|H9YBaqbmXM|w5ieH&mRW!ivo)O?F%G_-4IGfvIls2kd'
    '!=0y$Mi>y_y&ynB?VMwZ1<d%VIewaXl^^FZb9PCnkiA<Is&p$EggfyhZmh;p643&LazE&%MxJGa4_BGr&&^7ilQ3n?ba0R>aqVi<V-9aafy1Dc'
    'vrL;C8*nsX9A<HBR)NMPwdU`cy%jA50}MtvhPi%(5?C7)%v}Y^deSz*le$1%;X@wSg2#x)#esjC-_>D4Mt5FSxiD}++6v4u?8cm9!Q*JOs0LdL'
    'UZMJiT!+&+n;VFr^8F0(|0C>Q%@GU8Blodjytz$nTUQSQcEkVYrOx-jbQO>lvN|~Pjm7LMoCJRGk@f8?@<SBoVBBtx96K1HvMK_%N_sB5C(=1*'
    'LT5xk#A}Ske<2_t3LwnuFU&JbXx))-Js=q%6h&^HszzW4(X5%2gKHonB<3OWTl+rvijB1NvBvmvCi)@t0P&S&{Dmxq+fhOjZ4G~{dkB#cA;;Zw'
    '2iy_Ys}9v?xGw@Vu5ah6f7)ivHHQ@E!cFse7$5IZ9HJtqx&Q+kp+AN@3$ln?%(&Fa&-M9lXS4MRXo-V#OjjMbh)r>HgIEN29xI-H)zAa-$YA=6'
    'r$xhhTPZZX*m*nOt=bqId$SlKhTZoZNMxRZP8uf?kv;C-INJ?pme~L^kPx}ntZIg1{K|~DI5JJ-gQNRNtFzFl8FyluFF^1Wm+(dwt#bj5-U9zG'
    '$d^ntcK1*F<n^5S(*rMwgYZ;h)7*omtzcc%vumHHYOrHmk3;pLn~~)=+O`U#BAm<qC$s7bf2>1PZHA2MiWuv}-i{iN155@g|LGI+P1{B|Bu0;j'
    'We{^{oZ}bf-PIYWtwiTct{RW%G)~SPvgxbNaqFBapRE(lP5`6<gKL))BCkQ>^?y1uuYxD1i5Q#<b<Abq$}TQ8+9IF(_7m*j0tR|cRSA`%>e=C`'
    '7OjP3{ci4F9LKqBK)phnT?$cz+979z8q%<7Fe8%<S7T6w`#?D?>xrKj!N>e+c3+;YD#^(r=PT;nxX_eOg;WWM)%HTpWte1G(*^IPX&AIMuTqGz'
    '@NWM9H!;fF9fD`HQ5D&w*(I`xv;>KWxE4l>i=>?$>C_`Bh1NxJq-n<r5f9+whwRNBg7DUT9=uwggWsge29$CkeNaXxoi<44N4<c2L44fvmZ}D^'
    'av480hZnmHQV_7fE+j4aXBh+oZQ?>Orx?}7?e%msHSxI=%-`0O))@l>gjOH<?LLH9aG$|3cO+lOLZZ4+Cb$gnJ7zlpNv3I%nT^D_5-pG*YyvnO'
    'S+%crDug=`wVlyHgL5L#vpH7*;Gkh|Q$Mf-T>9ooq)(YVj(3>Pm=+dc|AW1Z=c!S@@2Dj*cd05bHNscpI2)BbAFHczhi*8*J<$#LLromj8^(FP'
    '+o7Wi<a)*Mb2FGu^w#2MxzwVrw8xHaS0^|1t<e$$dBLw;qFR$_Kl5PU?T7rY>gaH)7m&-*whgFC9G8LUK@$#h19L>|xsWg#C5|O~mDNtE<HL@L'
    'Ao`?82qO+valvV#AP<CA8YG0x+`IyIns_NBd*P#FBV<A~Bv?B3<(`U24uQZUjBDjCWStSQJl;Slw3sb?pjsW$eE@(4wd&kN`(C--dq3~GJhi6Y'
    'Q%GSaKI!_cr4VpyAWu$=MRXSsWpyAJxvvfL)S)R2#3j~Xz227*_%_~WfKn*#2RX*oti+l%z&Lo?$}L&mB645{A%LP=QL~zO?Rwts-25g~e6hFl'
    '%u2#O1f+vOE$=ADzjK_@NaUibS{j|<a2A=r(Q2Bhn0(zrVXg9R_eZ~;EH2p9vNK1pW=wF1{5;J21mnf!Xs88sug2!M)|X~AAWfJ#zTY2uL=x|I'
    '6DqtqXcfq*Be;vmO=xx@R=ABv-V(GU#ybZz8%iLcaFuU%kaYHaLS!9hHd9bX3i$&zda!u%9^j*2yj0*DlW}rKU05<;RLqri`(lsj8I;o0!sbRv'
    'Rw4$kgL1{oX&O4&2K?~gnm+7AJi!|XN=>5lVd&icaTiKu5SZQybTd&r4&|MoFvQv;L2w1ULOie>%1jk)b&%GI6}8@MuAjd2r+upDQ_eWvF9Ni#'
    '3jHO**T$odQ65=RwKlBCaP^ab%)$Bcfoo?HFMis|QXQlOZuw3P_9B(0hD=NYJ!*(gkOE#`q#UwU@K=%cn4GwQE{*B6PkUYR(IRPBz^-mNV<3nZ'
    'Xc6NHiu3wN<at$%!DCub4ZDVb^1@PqO!J%FFrjSga6W)EbCU0GCxIPJb3Vq$APAAiKq?%eNBS^7&){K^;H&-1{W9HtSll)FcJZ>&t0s9!<5pD('
    '<6_in1$9e+{lVi?P^V}L{4I2e&;GQdrc|-M@j=yd$4HRv`68gU3PPj@k1APBeWW1&2u5wntz@G6l*!MOw|j09KdMZl7>4dc&9k=0+0t!j(ph_S'
    'q%)V0i&T)R<=yVg*+fa;;hSB#NBZ<}bK2O!?doeF+Q3y;Yc=;1L94xhm3!4QT7b(%@l>1`vaSB~!C&m#J>`qzYQk9{nE?{n09VT~w#&Vra>+59'
    'HDOnsFp_py+U)?8clkN~Pdj@L6Cp4cG83bQywzZSCmwCh895=T8-LzC0Z$8o4gsk%to@O^OZ~X__l#EJWlcIJK)(kPxSW@Y&5(m6;hdWgx+)tl'
    '4|RJbadbo++#3Dc-9aV#a;|X8AaS!btce$lg$L`Gu3|_+*<rqm^g)@zj&<xz2n;A@e7S%42&#Sn2~zxYj~YA*EhG(65k>hp^b2T;MIb8TFon|;'
    '3IVPn;>#C1jG`(nPL*4fQ3>Vm&@BoPJs>*`VGt%TE}nC&gkO}2hmxmSF<RgHv<E5p#Wh>un6#}m(@aPjjc1XJ$hC0YY{z?ZsL#?<CpCAn0Oap6'
    '!nOCil+T<UawefP9rh&LM0q9Ulsk&PVRFnWMmIw=p36d3A+a>g-m(S<`>TD--=uS1?sV$a!`1o#ksB{z2e?&|5^hhxh$Dcqqo#Kcn#;9b(Y(Hp'
    'CnpC$CfSR<P(c${NFJ$15%1Q>kK-Z}7ERN+KD08YW|NxG#1c{#!Yk23w4|2px4WfJE4Uf3nwkb4!KF?N?s87XN*PyE;)3RTLS_!lHwO(10QXsF'
    'nSZ+SZ}(H55jN=i;3orDiL5F|TRwZ@VkVg%u>^<*Knpb4+<31YD}#DR#3^fD?zlc(1=K;)D&giT$?v4;_A8Fd+GiwYB4S7xh&E9((`!U%PCiH7'
    'hF5#C;y8>0NjW+H+K3T&nKws-JPTle_I^6TnCMJ$H$ZXkjne5F`EDcp%C4=l*)Xv{+%>h^<F>Pj(1NwhnSi)R5F$%UD?#&~Ct=-@lj#&S?yG&='
    '*L_+BTwR6PM%f@9d>7qYy_z8KWleQ^)u<5G4b!Z3L}*<rI;uDJ{{6r57VQs~qk9@}e1epq_o6gjJ^MZ6ySB^79t|!Y9B$M|q!xB=Y2Lor8&>h<'
    'wp1>f+?uBrIlLJ1LN%bTumvi+t(=$EsoF$(6-UQcyj18VjdA~e_gJ}&=pby=yVhU?fwcxEMKfh{<ebOR<j2*{;usqNiQ0vSRqU)K&h|_D%X%K-'
    'KwBc5Sj>bdiJm<y4H69)q9#tV1H-tCh%;Y}|2-U4t)BY0{p}9)Ptg)hBMr@uaoh!!&wY%*2Wr%2a$K<oBPE9&KrIyh7GP6(7tr_1J!)x&P_qR`'
    'JX?_d=$T)nf>lAgHSP#ycnc`LLEpSp*yfX5;DvS1{ja;&LJ;y{p>4F++<S|4607QuKXt2parPNmrNhu9)(W!|)Qz0)hdZo)zt8=w!`+%Dp41H0'
    '95a`0vE0<l)%4NCc~mltY`&MjhfLS<b&%<4IQ#Z@JK+yA^ADq{Q*m5TMj%BMah}fwgBnV_sm^g_E1uv{*CeTkS|zpqvRAHGC4yISjTZN+V5~@C'
    '&apXW2p_j%MhwS#GhwnkZIxHH#37-IsQB}4`ZM|KyJ0!niZdP+$>3Gr5#b%r*|$HPu~cUur#6zQ?3SJulA{6d`qO^9ptuwH<kqUq)$i_F{k3qF'
    '+Xb)ApQ29&pB?avgSXeL4@{VFR%o#Q{PD+s0o>8a?f'
)
XMLID = '{http://www.w3.org/XML/1998/namespace}id'

def sha(data): return hashlib.sha256(data).hexdigest()
def unpack(encoded): return zlib.decompress(base64.b85decode(encoded))
def cmd(*args,cwd=None):
    p=subprocess.run(args,cwd=cwd,capture_output=True,text=True)
    if p.returncode: raise RuntimeError(f"Commande en échec ({p.returncode}): {' '.join(map(str,args))}\n{p.stderr or p.stdout}")
    return p.stdout.strip()

def inspect_tree(root):
    ids=collections.Counter(); sphinx=[]; labels=[]; invalid=[]
    for path in sorted(root.rglob('*.ptx')):
        try: tree=ET.parse(path)
        except ET.ParseError as exc:
            invalid.append(f'{path.relative_to(root)}: {exc}'); continue
        for el in tree.iter():
            if el.get(XMLID): ids[el.get(XMLID)]+=1
            if el.tag=='url' and (el.get('href') or '').startswith('#'):
                sphinx.append({'file':str(path.relative_to(root)),'href':el.get('href')})
            if el.tag in ('pre','input','code') and el.text:
                for label in re.findall(r'\|\\label\{[^}\n]+\}\|',el.text):
                    labels.append({'file':str(path.relative_to(root)),'label':label})
    # Identifiants dupliqués entre fichiers peuvent provenir de fichiers non inclus
    return {'remaining_sphinx':sphinx,'remaining_labels':labels,'duplicate_ids':{k:v for k,v in ids.items() if v>1},'xml_errors':invalid}

def restore_graphs_references(staged):
    """Rétablir les liens perdus lors des premières corrections manuelles.

    Les renvois vers des lignes sont ramenés vers leur listing, sans inventer
    de numéro de ligne. Les ancres de ligne exactes restent à implémenter.
    """
    path = staged/'Advanced/GraphsRevisited.ptx'
    text = path.read_text(encoding='utf-8')
    operations = [
        ('Listing\u00a0the listing below', '<xref ref="lst_simplematcher"/>'),
        ('Listing\u00a0the corresponding listing', '<xref ref="lst_mismatchedlinks"/>'),
        ('Line\u00a0the comparison', '<xref ref="lst_simplematcher"/>'),
        ('line\u00a0the pattern reset', '<xref ref="lst_simplematcher"/>'),
        ('line\u00a0the end-of-text check', '<xref ref="lst_simplematcher"/>'),
        ('Line\u00a0the end-of-pattern check', '<xref ref="lst_simplematcher"/>'),
        ('Line\u00a0the dictionary initialization', '<xref ref="lst_mismatchedlinks"/>'),
    ]
    for old, new in operations:
        if text.count(old) != 1:
            raise RuntimeError(f'Restauration ambiguë ({old!r}): {text.count(old)} occurrence(s)')
        text = text.replace(old, new, 1)
    for name, signature in [
        ('lst_simplematcher', 'def simple_matcher(pattern, text):'),
        ('lst_mismatchedlinks', 'def mismatched_links(pattern):'),
    ]:
        found = list(re.finditer(r'<pre>(.*?)</pre>', text, flags=re.DOTALL))
        blocks = [(m, m.group(1)) for m in found if signature in m.group(1)]
        if len(blocks) != 1:
            raise RuntimeError(f'Listing {name} non identifié sans ambiguïté')
        match, code = blocks[0]
        listing = f'<listing xml:id="{name}"><program language="python" label="{name}"><input>{code}</input></program></listing>'
        text = text[:match.start()] + listing + text[match.end():]
    ET.fromstring(text)
    path.write_text(text, encoding='utf-8')
    return len(operations)

def repair_remaining_code_references(staged):
    """Convertit huit ancres Sphinx vers les listings PreTeXt existants.

    Le lien mène au listing entier lorsque l'ancre de ligne Sphinx n'existe
    plus ; ne prétend pas fournir un renvoi à une ligne exacte.
    """
    from lxml import etree
    mappings = {
        'Advanced/DictionariesRevisited.ptx': {
            '#check1:lst_skiplistsearchcode': 'lst_skiplistsearchcode',
            '#down1:lst_skiplistsearchcode': 'lst_skiplistsearchcode',
            '#check2:lst_skiplistsearchcode': 'lst_skiplistsearchcode',
            '#found:lst_skiplistsearchcode': 'lst_skiplistsearchcode',
            '#check3:lst_skiplistsearchcode': 'lst_skiplistsearchcode',
            '#down2:lst_skiplistsearchcode': 'lst_skiplistsearchcode',
            '#next1:lst_skiplistsearchcode': 'lst_skiplistsearchcode',
            '#init:lst_mapclass': 'lst_mapclass',
        }
    }
    count=0
    for rel, mapping in mappings.items():
        path=staged/rel
        tree=etree.parse(str(path))
        ids={e.get('{http://www.w3.org/XML/1998/namespace}id') for e in tree.iter()}
        if not set(mapping.values()) <= ids:
            raise RuntimeError('Listing cible absent dans '+rel)
        seen=set()
        for old in list(tree.xpath("//*[local-name()='url']")):
            href=old.get('href')
            if href not in mapping: continue
            if href in seen: raise RuntimeError('Ancre multiple : '+href)
            seen.add(href)
            new=etree.Element('xref',ref=mapping[href])
            new.tail=old.tail
            old.getparent().replace(old,new)
            count+=1
        if seen != set(mapping):
            raise RuntimeError('Ancres introuvables : '+repr(set(mapping)-seen))
        tree.write(str(path),encoding='utf-8')
    return count

def restore_commented_code_references(staged):
    """Restaure quatre liens Sphinx qui avaient été commentés.

    Ancre de repli sur le listing complet, non sur la ligne individuelle.
    """
    changes = {
        'Advanced/PythonListsRevisited.ptx': [
            ('line\u00a0 <!-- <url href="#line:lst_arr_size" visual="#line:lst_arr_size">[line:lst_arr_size]</url> -->',
             'the relevant condition in <xref ref="lst_arraylistinit"/>'),
            ('line\u00a0 <!--<url href="#line:lst_arr_cop1" visual="#line:lst_arr_cop1">[line:lst_arr_cop1]</url>. -->',
             'the copying loop in <xref ref="lst_arraylistinit"/>.'),
            ('line\u00a0<!-- <url href="#line:lst_arrlistins_range" visual="#line:lst_arrlistins_range">[line:lst_arrlistins_range]</url> -->',
             'the relevant statement in <xref ref="lst_arrlistins"/>'),
        ],
        'Advanced/RecursionRevisited.ptx': [
            ('line <!-- <url href="#line:gcd3_return" visual="#line:gcd3_return">[line:gcd3_return]</url> -->',
             'the return statement in <xref ref="lst_gcd3"/>'),
        ],
    }
    total=0
    for rel,repls in changes.items():
        path=staged/rel
        content=path.read_text(encoding='utf-8')
        for old,new in repls:
            matches=content.count(old)
            if matches!=1:
                raise RuntimeError(f'Renvoi absent ou ambigu {rel}: {old!r} ({matches})')
            content=content.replace(old,new,1)
            total+=1
        ET.fromstring(content)
        path.write_text(content,encoding='utf-8')
    return total


def generate_quantization_comparisons(project):
    """Deux figures originales et reproductibles, sans image ni paquet externe.

    Scène synthétique : ce ne sont PAS les figures historiques « bubbles.jpg ».
    Quantification simple conforme à simple_quant et partition octree adaptative
    à au plus 256 couleurs. PNG encodés avec la bibliothèque standard.
    """
    import math
    import heapq
    import struct
    import zlib

    w,h=216,144
    pixels=[]
    def clamp(x):
        return max(0,min(255,int(x)))
    for y in range(h):
        for x in range(w):
            t=y/h
            n=((x*37+y*73+(x*y)%97)*2654435761)&0xffffffff
            noise=((n>>16)&255)-128
            if y < 67+int(6*math.sin(x/25)):
                c=(32+73*t,119+81*t,184+55*t)
                d=noise*.11
            else:
                c=(48+32*t,105+27*(1-t),39+9*t)
                d=noise*.60
            # Maison et toit colorés, pour visualiser les contours.
            if 53 < x < 113 and 48 < y < 109:
                c=(172,117,78);d=noise*.20
            if 44 < x < 123 and 33 < y < 58 and y > 34+abs(x-83)*.52:
                c=(145,49,43);d=noise*.12
            if 79 < x < 92 and 77 < y < 109:
                c=(61,57,47);d=0
            # Arbre : feuillage texturé et tronc.
            if 163 < x < 174 and 58 < y < 120:
                c=(97,63,37);d=noise*.2
            if ((x-168)/34)**2+((y-54)/37)**2 < 1:
                c=(29+19*t,102+37*t,40);d=noise*.42
            pixels.append(tuple(clamp(v+d) for v in c))
    simple=[(r//36*36,g//42*42,b//42*42) for r,g,b in pixels]

    # Subdivision octree adaptative ; chaque nœud terminal est une couleur.
    # Les divisions suivent les trois bits de même rang des composantes RVB.
    groups={(0,0):list(range(len(pixels)))}
    serial=0
    queue=[]
    def score(indices,depth):
        if depth>=8 or len(indices)<=1:
            return 0.0
        m=len(indices)
        sums=[sum(pixels[i][c] for i in indices)/m for c in range(3)]
        variance=sum(sum((pixels[i][c]-sums[c])**2 for i in indices) for c in range(3))
        return variance
    heapq.heappush(queue,(-score(groups[(0,0)],0),0,0))
    while queue and len(groups)<256:
        negative,depth,ident=heapq.heappop(queue)
        key=(depth,ident)
        indices=groups.get(key)
        if indices is None or negative>=0 or depth==8: continue
        bit=7-depth
        children={}
        for i in indices:
            r,g,b=pixels[i]
            octant=(((r>>bit)&1)<<2)|(((g>>bit)&1)<<1)|((b>>bit)&1)
            children.setdefault(octant,[]).append(i)
        # Ne jamais dépasser le plafond de 256 couleurs.
        if len(groups)-1+len(children)>256: continue
        del groups[key]
        for octant,ix in sorted(children.items()):
            child=(depth+1,ident*8+octant)
            groups[child]=ix
            heapq.heappush(queue,(-score(ix,depth+1),child[0],child[1]))
    octree=[None]*len(pixels)
    for ix in groups.values():
        col=tuple(round(sum(pixels[i][c] for i in ix)/len(ix)) for c in range(3))
        for i in ix: octree[i]=col
    assert all(x is not None for x in octree) and len(groups)<=256

    def make_png(original,quantized):
        gap=8; outw=2*w+gap
        raw=bytearray()
        for y in range(h):
            raw.append(0)
            for rgb in original[y*w:(y+1)*w]:
                raw.extend(rgb)
            raw.extend(b'\xff'*(gap*3))
            for rgb in quantized[y*w:(y+1)*w]:
                raw.extend(rgb)
        def chunk(tag,data):
            return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data)&0xffffffff)
        return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',outw,h,8,2,0,0,0))
                +chunk(b'IDAT',zlib.compress(bytes(raw),9))+chunk(b'IEND',b''))
    dest=project/'assets/rm2'
    dest.mkdir(parents=True,exist_ok=True)
    (dest/'simple-quantization-comparison.png').write_bytes(make_png(pixels,simple))
    (dest/'octree-quantization-comparison.png').write_bytes(make_png(pixels,octree))
    return len(groups)


def attach_quantization_figures(staged):
    """Rétablit les deux figures PreTeXt et leurs références cliquables."""
    from lxml import etree
    path=staged/'Advanced/TreesRevisited.ptx'
    tree=etree.parse(str(path))
    specs=[
        ('#fig_simplecompare','fig-simplecompare',
         'Simple color quantization: original (left) and quantized image (right); reproducible synthetic example',
         'rm2/simple-quantization-comparison.png'),
        ('#fig_otquantcompare','fig-otquantcompare',
         'Octree quantization: original (left) and quantized image (right); reproducible synthetic example',
         'rm2/octree-quantization-comparison.png'),
    ]
    for oldref,newid,caption,source in specs:
        urls=tree.xpath("//*[local-name()='url' and @href=$ref]",ref=oldref)
        if len(urls)!=1: raise RuntimeError(f'Figure à rétablir : {oldref}: {len(urls)} renvois')
        link=urls[0];parent=link.getparent()
        # Le mot « Figure » existe déjà juste avant <url>.
        index=parent.index(link)
        owner=parent if index==0 else parent[index-1]
        attr='text' if index==0 else 'tail'
        before=getattr(owner,attr) or ''
        before2,n=re.subn(r'Figure(?:\s|\u00a0)+$', '', before, count=1)
        if n!=1: raise RuntimeError('Préfixe Figure introuvable pour '+oldref)
        setattr(owner,attr,before2)
        xref=etree.Element('xref',ref=newid)
        xref.tail=link.tail
        parent.replace(link,xref)
        para=parent
        while para is not None and etree.QName(para).localname!='p':
            para=para.getparent()
        if para is None: raise RuntimeError('Paragraphe cible introuvable')
        figure=etree.Element('figure')
        figure.set('{http://www.w3.org/XML/1998/namespace}id',newid)
        etree.SubElement(figure,'caption').text=caption
        etree.SubElement(figure,'image',source=source,width='95%')
        holder=para.getparent()
        holder.insert(holder.index(para)+1,figure)
    tree.write(str(path),encoding='utf-8')
    return len(specs)


def update_quantization_caption_text(staged):
    """Adapte la description des figures synthétiques au contenu réel."""
    path=staged/'Advanced/TreesRevisited.ptx'
    original=path.read_text(encoding='utf-8')
    begin=' shows a before and\n                after comparison of original and quantized images.'
    end='to two shades of tan.'
    i=original.find(begin)
    j=original.find(end,i)
    if i<0 or j<0 or original.find(begin,i+1)>=0:
        raise RuntimeError('Paragraphe de quantification simple introuvable ou ambigu')
    new=(' shows the original synthetic scene on the left and the result of '
         'simple color quantization on the right. The sky, house, tree, and '
         'textured ground make it possible to compare changes in color levels '
         'and fine detail. This illustrative scene was generated for the RM2 '
         'edition; it replaces the unavailable historical photograph. '
         'To experiment with a real photograph, you can run the '
         '<c>simple_quant</c> program on a JPEG image of your choice.')
    revised=original[:i]+new+original[j+len(end):]
    ET.fromstring(revised)
    path.write_text(revised,encoding='utf-8')
    return 1


def install_table_spacing_xsl(project):
    """Style PDF RM2 : réduire l'espacement des colonnes."""
    xsl = r'''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:import href="./core/pretext-latex.xsl"/>
  <xsl:param name="latex.preamble.late">
    <xsl:text>&#10;% RM2 table padding&#10;</xsl:text>
    <xsl:text>\\setlength{\\tabcolsep}{2pt}&#10;</xsl:text>
    <xsl:text>% RM2: two long titles get visual line breaks only&#10;</xsl:text>
    <xsl:text>\titleformat{\section}[hang]{\divisionfont\Large\bfseries}{\thesection\ptxappendixperiodsection}{1ex}{\ifstrequal{#1}{Why Study Data Structures and Abstract Data Types?}{\shortstack[l]{Why Study Data Structures\\and Abstract Data Types?}}{#1}}[{\large\authorsptx}]&#10;</xsl:text>
    <xsl:text>\titleformat{\chapter}[display]{\divisionfont\huge\bfseries}{\divisionnameptx\space\thechapter}{20pt}{\Huge\ifstrequal{#1}{Graphs and Graphing Algorithms}{\shortstack[l]{Graphs and\\Graphing Algorithms}}{#1}}[{\Large\authorsptx}]&#10;</xsl:text>
  </xsl:param>
</xsl:stylesheet>
'''
    ET.fromstring(xsl)
    path=project/'xsl/rm2-tables.xsl'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(xsl,encoding='utf-8')
    return path


def configure_project(path):
    tree=ET.parse(path); root=tree.getroot()
    targets=root.find('targets')
    if targets is None: raise RuntimeError('project.ptx sans <targets>')
    for name,fmt in [('rm2','pdf'),('rm2-latex','latex')]:
        t=next((x for x in targets.findall('target') if x.get('name')==name),None)
        if t is None: t=ET.SubElement(targets,'target',{'name':name})
        t.attrib.update({'format':fmt,'source':'../pretext-rm2/main.ptx','publication':'publication-rm2.ptx'})
        # PreTeXt 2.56 attend @xsl, relatif au dossier xsl/ du projet.
        # Supprimer les anciens éléments <xsl> mal formés créés auparavant.
        for obsolete in list(t.findall('xsl')):
            t.remove(obsolete)
        t.set('xsl','rm2-tables.xsl')
    ET.indent(tree, space='  ')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--project',type=Path,required=True,help='Répertoire cible (créé par git clone si absent)')
    ap.add_argument('--repo',default='https://github.com/RunestoneInteractive/pythonds.git',help='URL Git source')
    ap.add_argument('--dry-run',action='store_true',help='Aucune écriture ni compilation')
    ap.add_argument('--build',action='store_true',default=True,help='Compiler (activé par défaut)')
    ap.add_argument('--no-build',dest='build',action='store_false',help='Ne pas compiler')
    ap.add_argument('--archive',action='store_true',default=True,help='Archiver (activé par défaut)')
    ap.add_argument('--no-archive',dest='archive',action='store_false',help='Ne pas archiver')
    ap.add_argument('--revision',help='Exiger ce SHA de commit Git pour figer le point de départ')
    args=ap.parse_args(); project=args.project.expanduser().resolve()
    if not project.exists():
        if args.dry_run:
            print(f'[simulation] git clone {args.repo} {project}')
            return 0
        project.parent.mkdir(parents=True, exist_ok=True)
        print('Clonage des sources originales :', args.repo, flush=True)
        subprocess.run(['git', 'clone', args.repo, str(project)], check=True)
    elif not (project/'.git').exists():
        ap.error(f'Le chemin existe mais n’est pas un dépôt Git : {project}')
    if not (project/'pretext/main.ptx').is_file() or not (project/'project.ptx').is_file():
        ap.error('Projet PreTeXt introuvable dans le clone')
    if args.revision:
        # La révision est choisie avant l’export. Aucune modification de pretext/.
        if not args.dry_run:
            if cmd('git','status','--porcelain','--untracked-files=no',cwd=project):
                ap.error('Dépôt modifié : impossible de changer de révision sans risque')
            subprocess.run(['git','fetch','origin',args.revision],cwd=project,check=True)
            subprocess.run(['git','checkout','--detach',args.revision],cwd=project,check=True)
        else:
            print('[simulation] checkout de la révision :',args.revision)
    revision=cmd('git','rev-parse','HEAD',cwd=project)
    if args.revision and not revision.startswith(args.revision):
        ap.error(f'Révision incompatible : {revision} != {args.revision}')
    data=json.loads(unpack(PAYLOAD))
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    print('Révision Git :',revision)
    print('Fichiers de contenu modifiés embarqués :',len(data['overlays']))
    print('Ressources RM2 embarquées :',len(data['assets']))
    if args.dry_run:
        print('Simulation seulement ; aucune modification.')
        return 0

    report_dir=project/'audit-rm2'/f'reproduction-{stamp}'
    report_dir.mkdir(parents=True,exist_ok=False)
    # Extraire les fichiers de la révision Git plutôt que recopier les changements locaux.
    with tempfile.TemporaryDirectory(prefix='rm2-base-') as d:
        base=Path(d)
        with (base/'pretext.tar').open('wb') as f:
            p=subprocess.run(['git','archive','--format=tar','HEAD','pretext'],cwd=project,stdout=f,stderr=subprocess.PIPE)
        if p.returncode: raise RuntimeError('git archive a échoué : '+p.stderr.decode(errors='replace'))
        with tarfile.open(base/'pretext.tar') as t:
            t.extractall(base,filter='data')
        src=base/'pretext'
        expected=set(data['rm2_inventory'])
        found={str(p.relative_to(src)) for p in src.rglob('*.ptx')}
        if not expected <= found:
            raise RuntimeError('Fichiers originaux absents du commit : '+repr(sorted(expected-found)[:12]))
        # Le reste est copié depuis le commit Git : fichiers strictement tracés.
        staged=base/'pretext-rm2'
        shutil.copytree(src,staged)
        for rel,blob in data['overlays'].items():
            p=staged/rel; p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(unpack(blob))
        got={str(p.relative_to(staged)):sha(p.read_bytes()) for p in staged.rglob('*.ptx')}
        bad={k:(data['source_hashes'][k],got.get(k)) for k in expected if data['source_hashes'][k]!=got.get(k)}
        if bad: raise RuntimeError('La base Git diffère du contenu validé : '+repr(dict(list(bad.items())[:12])))
        restored_graphs=restore_graphs_references(staged)
        repaired_code_refs=repair_remaining_code_references(staged)
        restored_commented_refs=restore_commented_code_references(staged)
        restored_figures=attach_quantization_figures(staged)
        updated_descriptions=update_quantization_caption_text(staged)
        problems=inspect_tree(staged)
        if problems['xml_errors']: raise RuntimeError('XML invalide : '+repr(problems['xml_errors']))
        # Sauvegarde et remplacement atomique du dossier RM2 (jamais pretext/).
        dest=project/'pretext-rm2'
        if dest.exists():
            backup=report_dir/'pretext-rm2-before'
            shutil.copytree(dest,backup)
            shutil.rmtree(dest)
        shutil.copytree(staged,dest)
    # Assets et publication : ne remplacer que les éléments spécifiques à RM2.
    for rel,blob in data['assets'].items():
        path=project/rel;path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and sha(path.read_bytes()) != data['asset_hashes'][rel]:
            bak=report_dir/'previous-assets'/rel;bak.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,bak)
        path.write_bytes(unpack(blob))
    octree_colors=generate_quantization_comparisons(project)
    install_table_spacing_xsl(project)
    project_file=project/'project.ptx'
    new_project=configure_project(project_file)
    if project_file.read_bytes()!=new_project:
        shutil.copy2(project_file,report_dir/'project-before.ptx')
        project_file.write_bytes(new_project)
    report={'datetime':stamp,'git_revision':revision,'overlay_files':sorted(data['overlays']),
            'asset_files':sorted(data['assets']),**problems}
    print('Références cliquables restaurées (Graphes) :',restored_graphs)
    print('Ancres de code converties en liens vers les listings :',repaired_code_refs)
    print('Anciens liens masqués restaurés :',restored_commented_refs)
    print('Figures comparatives et renvois PreTeXt restaurés :',restored_figures,'; couleurs octree :',octree_colors)
    print('Descriptions des figures adaptées :',updated_descriptions)
    print('Réédition reproduite. Références Sphinx résiduelles :',len(problems['remaining_sphinx']))
    print('Marqueurs de code résiduels :',len(problems['remaining_labels']))
    if args.build:
        log=report_dir/'build.log'
        with log.open('w') as f:
            p=subprocess.run(['uvx','--from','pretext','pretext','build','rm2'],cwd=project,stdout=f,stderr=subprocess.STDOUT)
        content=log.read_text(errors='replace');last=content.rsplit('This is XeTeX, Version',1)[-1]
        widths=[float(v) for v in re.findall(r'Overfull \\hbox \(([\d.]+)pt too wide\)',last)]
        report['build']={'returncode':p.returncode,'horizontal':len(widths),'max_pt':max(widths,default=0),
                         'vertical':last.count(r'Overfull \vbox'),
                         'pages':re.findall(r'Output written on main\.pdf \((\d+) pages?',last)}
        print('PDF :',report['build'])
    if args.archive:
        dest=report_dir/f'pythonds-rm2-sources-{stamp}.tar.gz'
        with tarfile.open(dest,'w:gz') as t:
            for rel in ['pretext-rm2','project.ptx','publication/publication-rm2.ptx','assets/rm2','xsl/rm2-tables.xsl']:
                t.add(project/rel,arcname=rel)
        print('Archive :',dest)
    (report_dir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    md=[f'# Reproduction RM2 — {stamp}', '', f'Révision Git : `{revision}`',
        f'Fichiers modifiés par rapport au dépôt : {len(data["overlays"])}',
        f'Références Sphinx résiduelles : {len(problems["remaining_sphinx"])}',
        f'Marqueurs résiduels : {len(problems["remaining_labels"])}',
        f'Identifiants dupliqués dans les .ptx : {len(problems["duplicate_ids"])}','']
    if 'build' in report: md += ['## Compilation', '```json',json.dumps(report['build'],indent=2),'```','']
    md += ['## Références à examiner',*['- '+x['file']+': '+x['href'] for x in problems['remaining_sphinx']]]
    (report_dir/'report.md').write_text('\n'.join(md)+'\n')
    print('Rapport :',report_dir/'report.md')
    if 'build' in report and (report['build']['returncode']!=0 or report['build']['vertical']):return 2
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e: print('ÉCHEC :',e,file=sys.stderr);sys.exit(1)
