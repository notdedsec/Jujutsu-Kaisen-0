#!C:/KaizokuEncoder/python

import vapoursynth as vs
from vardautomation import (
    X265Encoder, QAACEncoder, Eac3toAudioExtracter, EztrimCutter,
    FileInfo, VPath, Preset, RunnerConfig, SelfRunner, Mux
)

import lvsfunc as lvf
import awsmfunc as awf
import havsfunc as haf
import kagefunc as kgf
import vardefunc as vdf
from debandshit import dumb3kdb
from xvs import WarpFixChromaBlend
from adptvgrnMod import adptvgrnMod
from vsutil import depth, iterate, get_y

core = vs.core

PresetCustom = Preset(
    idx=core.lsmas.LWLibavSource,
    a_src=VPath('{work_filename:s}_track_{track_number:s}.flac'),
    a_src_cut=VPath('{work_filename:s}_cut_track_{track_number:s}.flac'),
    a_enc_cut=VPath('{work_filename:s}_cut_enc_track_{track_number:s}.m4a'),
    chapter=VPath('chapters.txt'),
    preset_type=0
)

JPBD = FileInfo('00000.m2ts', (24, -24), preset=PresetCustom)


def selective_aa(clip: vs.VideoNode, thr: list = [750, 1500, 500]):
    clip = depth(clip, 16)
    luma = get_y(clip)

    mask = luma.tcanny.TCanny(sigma=.5, t_h=6, t_l=3, mode=0)
    mask = mask.std.Maximum(coordinates=[1, 0, 1, 0, 0, 1, 0, 1]).std.Deflate()

    eeaa = lvf.aa.taa(luma, lvf.aa.eedi3())
    nnaa = lvf.aa.taa(luma, lvf.aa.nnedi3())

    expr_nn = f'y x - {thr[0]} > x {thr[0]} + y x - -{thr[1]} < x {thr[1]} - y ? ?'
    expr_ee = f'z x - {thr[0]} > x {thr[0]} + z x - -{thr[1]} < x {thr[1]} - z ? ?'
    expr_nnee = f'y z - abs {thr[2]} > {expr_ee} {expr_nn} ?'

    nnee = core.std.Expr([luma, nnaa, eeaa], expr_nnee)
    nnee = core.std.MaskedMerge(luma, nnee, mask)
    nnee = vdf.misc.merge_chroma(nnee, clip)

    return nnee


def filtering(clip: vs.VideoNode = JPBD.clip_cut):
    clip = depth(clip, 16)
    crop = core.std.Crop(clip, 0, 0, 138, 138)
    crop = core.resize.Point(crop, src_top=-1, resample_filter_uv='bicubic')
    edge = awf.bbmod(crop, 0, 2, 0, 0, planes=[1, 2])

    mask = kgf.retinex_edgemask(edge, 2).std.Binarize(8500)
    mask = iterate(mask, core.std.Inflate, 4)

    denoise = haf.SMDegrain(edge, tr=3, thSAD=64, thSADC=48, RefineMotion=True)
    denoise = core.std.MaskedMerge(denoise, edge, mask)
    decsiz = vdf.noise.decsiz(denoise, min_in=45000, max_in=55000)

    aa = selective_aa(decsiz)
    clean = haf.EdgeCleaner(aa, strength=8, smode=1, hot=True)
    cwarp = WarpFixChromaBlend(clean, thresh=96)
    clean = core.std.Expr([aa, cwarp], 'x y min')

    deband = dumb3kdb(clean, radius=16, threshold=24)
    deband = core.std.MaskedMerge(deband, clean, mask)

    exclude = lvf.rfs(deband, decsiz, ranges=[(0, 640), (137735, 149000)])
    grain = adptvgrnMod(exclude, strength=0.25, sharp=60, static=True)
    final = depth(grain, 10)

    # return lvf.comp(crop, final, [x for x in range(1, len(crop)) if x % 69 == 0])
    return final


if __name__ == '__main__':
    config = RunnerConfig(
        X265Encoder('settings'),
        a_extracters = [
            Eac3toAudioExtracter(JPBD, track_in=2, track_out=1),
            Eac3toAudioExtracter(JPBD, track_in=3, track_out=2)
        ],
        a_cutters = [
            EztrimCutter(JPBD, track=1),
            EztrimCutter(JPBD, track=2)
        ],
        a_encoders = [
            QAACEncoder(JPBD, track=1),
            QAACEncoder(JPBD, track=2)
        ],
        muxer = Mux(JPBD)
    )

    brr = SelfRunner(filtering(), JPBD, config)
    brr.run()
    brr.do_cleanup()
    brr.rename_final_file('jjk0_premux.mkv')

else:
    filtering().set_output()

