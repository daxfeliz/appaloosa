'''
Routines to do analysis on the appaloosa flare finding runs. Including
  - plots for the paper
  - check against other sample of flares from Kepler
  - completeness and efficiency tests against FBEYE results
  - completeness and efficiency tests against fake data (?)


  Run on WWU workstation in dir:
  ~/research/kepler-flares/
'''

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import LogNorm
import matplotlib
from scipy.stats import binned_statistic_2d
from os.path import expanduser
import os
import appaloosa
import pandas as pd
import datetime
import warnings
from scipy.optimize import curve_fit


matplotlib.rcParams.update({'font.size':18})
matplotlib.rcParams.update({'font.family':'serif'})


def _ABmag2flux(mag, zeropt=48.60,
                wave0=6400.0, fwhm=4000.0):
    '''
    Replicate the IDL procedure:
    http://idlastro.gsfc.nasa.gov/ftp/pro/astro/mag2flux.pro
    flux = 10**(-0.4*(mag +2.406 + 4*np.log10(wave0)))

    Parameters set for Kepler band specifically
    e.g. see http://stev.oapd.inaf.it/~lgirardi/cmd_2.7/photsys.html
    '''

    c = 2.99792458e18 # speed of light, in [A/s]

    # standard equation from Oke & Gunn (1883)
    # has units: [erg/s/cm2/Hz]
    f_nu = 10.0 ** ( (mag + zeropt) / (-2.5) )

    # has units of [erg/s/cm2/A]
    f_lambda = f_nu * c / (wave0**2.0)

    # Finally: units of [erg/s/cm2]
    flux = f_lambda * fwhm
    # now all we'll need downstream is the distance to get L [erg/s]

    return flux


def _Perror(n, full=False, down=False):
    '''
    Calculate the asymmetric Poisson error, using Eqn 7
    and Eqn 12 in Gehrels 1986 ApJ, 3030, 336

    Parameters
    ----------
    n
    full

    Returns
    -------

    '''

    # if n > 0:

    err_dn = np.abs(n*(1.-1./(9.*n)-1./(3.*np.sqrt(n)))**3.-n)
    err_up = n+np.sqrt(n+0.75)+1.0-n

    # else:
    #     err_up = err_dn = np.nan

    if full is True:
        return err_dn, err_up
    else:
        if down is True:
            return err_dn
        else:
            return err_up


def _DistModulus(m_app, M_abs):
    '''
    Trivial wrapper to invert the classic equation:
    m - M = 5 log(d) - 5

    Parameters
    ----------
    m_app
        apparent magnitude
    M_abs
        absolute magnitude

    Returns
    -------
    distance, in pc
    '''
    mu = m_app - M_abs
    dist = 10.0**(mu/5.0 + 1.0)
    return dist


def _linfunc(x, m, b):
    '''
    A simple linear function to fit with curve_fit
    '''
    return m * x + b


def _plaw(x, m, b):
    x2 = 10.**x
    return b * (x2**m)


def fbeye_compare(apfile='9726699.flare', fbeyefile='gj1243_master_flares.tbl'):
    '''
    compare flare finding and properties between appaloosa and FBEYE
    '''

    # read the aprun output
    # t_start, t_stop, t_peak, amplitude, FWHM, duration, t_peak_aflare1, t_FWHM_aflare1,
    # amplitude_aflare1, flare_chisq, KS_d_model, KS_p_model,
    # KS_d_cont, KS_p_cont, Equiv_Dur
    apdata = np.loadtxt(apfile, delimiter=',', dtype='float', skiprows=5, comments='#')




    # index of flare start in "gj1243_master_slc.dat"
    # index of flare stop in "gj1243_master_slc.dat"
    # t_start
    # t_stop
    # t_peak
    # t_rise
    # t_decay
    # flux peak (in fractional flux units)
    # Equivalent Duration (ED) in units of per seconds
    # Equiv. Duration of rise (t_start to t_peak)
    # Equiv. Duration of decay (t_peak to t_stop)
    # Complex flag (1=classical, 2=complex) by humans
    # Number of people that identified flare event exists
    # Number of people that analyzed this month
    # Number of flare template components fit to event (1=classical >1=complex)

    # read the FBEYE output
    fbdata = np.loadtxt(fbeyefile, comments='#', dtype='float')


    # step thru each FBEYE flare
    # A) was it found by appaloosa?
    # B) how many events overlap?
    # C) compare the total computed ED's.
    # D) compare the start and stop times.
    for i in range(0, len(fbdata[0,:])):
        # find any appaloosa flares that overlap the FBEYE start/stop times
        # 4 cases to catch: left/right overlaps, totally within, totally without
        x_ap = np.where(((apdata[0,:] <= fbdata[2,i]) & (apdata[1,:] >= fbdata[3,i])) |
                        ((apdata[0,:] >= fbdata[2,i]) & (apdata[0,:] <= fbdata[3,i])) |
                        ((apdata[1,:] >= fbdata[2,i]) & (apdata[1,:] <= fbdata[3,i]))
                        )


    return


def k2_mtg_plots(rerun=False, outfile='plotdata_v2.csv'):
    '''
    Some quick-and-dirty results from the 1st run for the K2 science meeting

    run from dir (at UW currently)
      /astro/store/tmp/jrad/nsf_flares/-HEX-ID-/

    can run as:
      from appaloosa import analysis
      analysis.k2_mtsg_plots()

    '''

    # have list of object ID's to run (from the Condor run)
    home = expanduser("~")
    dir = home + '/Dropbox/research_projects/nsf_flare_code/'
    obj_file = 'get_objects.out'

    kid = np.loadtxt(dir + obj_file, dtype='str',
                     unpack=True, skiprows=1, usecols=(0,))

    if rerun is True:

        # read in KIC file w/ colors
        kic_file = '../kic-phot/kic.txt.gz'
        kic_g, kic_r, kic_i  = np.genfromtxt(kic_file, delimiter='|', unpack=True,dtype=float,
                                            usecols=(5,6,7), filling_values=-99, skip_header=1)
        kicnum = np.genfromtxt(kic_file, delimiter='|', unpack=True,dtype=str,
                               usecols=(15,), skip_header=1)
        print('KIC data ingested')

        # (Galex colors too?)
        #

        # (list of rotation periods?)
        p_file = '../periods/Table_Periodic.txt'
        pnum = np.genfromtxt(p_file, delimiter=',', unpack=True,dtype=str, usecols=(0,),skip_header=1)
        prot = np.genfromtxt(p_file, delimiter=',', unpack=True,dtype=float, usecols=(4,),skip_header=1)
        print('Period data ingested')

        gi_color = np.zeros(len(kid)) - 99.
        ri_color = np.zeros(len(kid)) - 99.
        r_mag = np.zeros(len(kid)) - 99.
        periods = np.zeros(len(kid)) - 99.

        # keep a few different counts
        n_flares1 = np.zeros(len(kid))
        n_flares2 = np.zeros(len(kid))
        n_flares3 = np.zeros(len(kid))
        n_flares4 = np.zeros(len(kid))

        print('Starting loop through aprun files')
        for i in range(0, len(kid)):

            # read in each file in turn
            fldr = kid[i][0:3]
            outdir = 'aprun/' + fldr + '/'
            apfile = outdir + kid[i] + '.flare'

            try:
                data = np.loadtxt(apfile, delimiter=',', dtype='float',
                                  comments='#',skiprows=4)

                # if (i % 10) == 0:
                #     print(i, apfile, data.shape)

                # select "good" flares, count them
                '''
                t_start, t_stop, t_peak, amplitude, FWHM,
                duration, t_peak_aflare1, t_FWHM_aflare1, amplitude_aflare1,
                flare_chisq, KS_d_model, KS_p_model, KS_d_cont, KS_p_cont, Equiv_Dur
                '''

                if data.ndim == 2:
                    # a quality cut
                    good1 = np.where((data[:,9] >= 10) &  # chisq
                                     (data[:,14] >= 0.1)) # ED
                    # a higher cut
                    good2 = np.where((data[:,9] >= 15) &  # chisq
                                     (data[:,14] >= 0.2)) # ED
                    # an amplitude cut
                    good3 = np.where((data[:,3] >= 0.005) & # amplitude
                                     (data[:,13] <= 0.05))   # KS_p
                    # everything cut
                    good4 = np.where((data[:,3] >= 0.005) &
                                     (data[:,13] <= 0.05) &
                                     (data[:,9] >= 15))

                    n_flares1[i] = len(good1[0])
                    n_flares2[i] = len(good2[0])
                    n_flares3[i] = len(good3[0])
                    n_flares4[i] = len(good4[0])

            except IOError:
                print(apfile + ' was not found!')

            # match whole object ID to colors
            km = np.where((kicnum == kid[i]))

            if (len(km[0])>0):
                gi_color[i] = kic_g[km[0]] - kic_i[km[0]]
                ri_color[i] = kic_r[km[0]] - kic_i[km[0]]

            pm = np.where((pnum == kid[i]))

            if (len(pm[0])>0):
                periods[i] = prot[pm[0]]

            if (i % 1000) == 0:
                outdata = np.asarray([n_flares1, n_flares2, n_flares3, n_flares4,
                                      gi_color, ri_color, periods])
                np.savetxt(outfile, outdata.T, delimiter=',')
                print(i, len(kid))

        # save to output lists
        outdata = np.asarray([n_flares1, n_flares2, n_flares3, n_flares4,
                              gi_color, ri_color, periods])
        np.savetxt(outfile, outdata.T, delimiter=',')

    else:
        print('Reading previous results')
        n_flares1, n_flares2, n_flares3, n_flares4, gi_color, ri_color, periods = \
            np.loadtxt(outfile, delimiter=',', dtype='float', unpack=True)



    # goal plots:
    # 1. color vs flare rate
    # 2. galex-g color vs flare rate
    # 3. g-r color vs period, point size/color with flare rate

    #---
    clr = np.log10(n_flares4)
    clr[np.where((clr > 3))] = 3
    clr[np.where((clr < 1))] = 1

    ss = np.argsort(clr)

    cut = np.where((clr[ss] >= 1.2))


    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.size'] = 14

    plt.figure()
    plt.scatter(gi_color[ss][cut], periods[ss][cut], alpha=.7, lw=0,
                c=clr[ss][cut], cmap=plt.cm.afmhot_r, s=50)
    plt.xlabel('g-i (mag)')
    plt.ylabel('Rotation Period (days)')
    plt.yscale('log')
    plt.xlim((0,3))
    plt.ylim((0.1,100))
    cb = plt.colorbar()
    cb.set_label('log # flares')
    plt.show()


    #---
    clr = np.log10(n_flares4)
    clr[np.where((clr > 2.2))] = 2.2
    clr[np.where((clr < 1))] = 1

    bin2d, xx, yy,_ = binned_statistic_2d(gi_color, np.log10(periods),
                                          clr, statistic='median',
                                          range=[[-1,4],[-1,2]], bins=75)

    plt.figure()
    plt.imshow(bin2d.T, interpolation='nearest',aspect='auto', origin='lower',
               extent=(xx.min(),xx.max(),yy.min(),yy.max()),
               cmap=plt.cm.afmhot_r)

    plt.xlim((0,3))
    plt.ylim((-1,2))
    plt.xlabel('g-i (mag)')
    plt.ylabel('log Period (days)')
    cb = plt.colorbar()
    cb.set_label('log # flares (median)')
    plt.show()


    return


def compare_2_lit(outfile='plotdata_v2.csv'):
    '''
    Things to show:
    1) my flare rates compared to literature values for same stars
    2) literature values for same stars compared to eachother

    '''
    # read in MY flare sample
    n_flares1, n_flares2, n_flares3, n_flares4, gi_color, ri_color, periods = \
        np.loadtxt(outfile, delimiter=',', dtype='float', unpack=True)

    # read in the KIC numbers
    home = expanduser("~")
    dir = home + '/Dropbox/research_projects/nsf_flare_code/'
    obj_file = 'get_objects.out'

    kid = np.loadtxt(dir + obj_file, dtype='str',
                     unpack=True, skiprows=1, usecols=(0,))


    #######################
    # Compare 2 Literature
    #######################
    pitkin = dir + 'comparison_datasets/pitkin2014/table2.dat'
    pid,pnum = np.loadtxt(pitkin, unpack=True, usecols=(0,1),dtype='str')
    pnum = np.array(pnum, dtype='float')
    p_flares = np.zeros(len(kid))

    balona = dir + 'comparison_datasets/balona2015/table1.dat'
    bid_raw = np.loadtxt(balona, dtype='str', unpack=True, usecols=(0,), comments='#')
    bid,bnum = np.unique(bid_raw, return_counts=True)
    b_flares = np.zeros(len(kid))

    shibayama = dir + 'comparison_datasets/shibayama2013/apjs483584t7_mrt.txt'
    sid_raw = np.loadtxt(shibayama, dtype='str', unpack=True, usecols=(0,), comments='#')
    sid,snum = np.unique(sid_raw, return_counts=True)
    s_flares = np.zeros(len(kid))

    for i in range(0,len(kid)):
        x1 = np.where((kid[i] == pid))
        if len(x1[0]) > 0:
            p_flares[i] = pnum[x1]

        x2 = np.where((kid[i] == bid))
        if len(x2[0]) > 0:
            b_flares[i] = bnum[x2]

        x3 = np.where((kid[i] == sid))
        if len(x3[0]) > 0:
            s_flares[i] = snum[x3]




    plt.figure()
    plt.scatter(p_flares, n_flares4)
    plt.scatter(b_flares, n_flares4,c='r')
    plt.scatter(s_flares, n_flares4,c='g')
    plt.show()

    # plt.figure()
    # plt.scatter(p_flares, b_flares)
    # plt.xlabel('Pitkin')
    # plt.ylabel('Balona')
    # plt.show()

    return


def benchmark(objectid='gj1243_master', fbeyefile='gj1243_master_flares.tbl'):

    # run data thru the normal appaloosa flare-finding methodology
    appaloosa.RunLC(objectid, display=False, readfile=True)

    apfile = 'aprun/' + objectid[0:3] + '/' + objectid + '.flare'
    apdata = np.loadtxt(apfile, delimiter=',', dtype='float',
                        comments='#',skiprows=4)

    fbdata = np.loadtxt(fbeyefile, comments='#', dtype='float')
    '''
    t_start, t_stop, t_peak, amplitude, FWHM,
    duration, t_peak_aflare1, t_FWHM_aflare1, amplitude_aflare1,
    flare_chisq, KS_d_model, KS_p_model, KS_d_cont, KS_p_cont, Equiv_Dur
    '''

    time = np.loadtxt(objectid + '.lc.gz', usecols=(1,), unpack=True)
    fbtime = np.zeros_like(time)
    aptime = np.zeros_like(time)

    for k in range(0,len(apdata[:,0])):
        x = np.where((time >= apdata[k,0]) & (time <= apdata[k,1]))
        aptime[x] = 1

    for k in range(0,len(fbdata[:,0])):
        x = np.where((time >= fbdata[k,0]) & (time <= fbdata[k,1]))
        fbtime[x] = 1

    # 4 things to measure:
    # num flares recovered / num in FBEYE
    # num time points recovered / time in FBEYE
    # % of FBEYE flare time recovered (time overlap)
    # % of specific FBEYE flares recovered at all (any overlap)


    n1 = float(len(apdata[:,0])) / float(len(fbdata[:,0]))
    n2 = float(np.sum(aptime)) / float(np.sum(fbtime))

    n3 = float(np.sum((fbtime == 1) & (aptime == 1))) / float(np.sum(fbtime == 1))
    n4_i = np.zeros_like(fbdata[:,0])


    for i in range(0, len(fbdata[:,0])):

        # find ANY overlap
        x_any = np.where(((apdata[:,0] <= fbdata[i,2]) & (apdata[:,1] >= fbdata[i,3])) |
                         ((apdata[:,0] >= fbdata[i,2]) & (apdata[:,0] <= fbdata[i,3])) |
                         ((apdata[:,1] >= fbdata[i,2]) & (apdata[:,1] <= fbdata[i,3]))
                         )
        if (len(x_any[0]) > 0):
            n4_i[i] = 1

    n4 = float(np.sum(n4_i)) / float(len(fbdata[:,0]))


    return (len(apdata[:,0]), len(fbdata[:,0]), n1, n2, n3, n4)


def paper1_plots(condorfile='condorout.dat.gz',
                 kicfile='kic.txt.gz', statsfile='stats.txt',
                 rerun=False, figdir='figures/', figtype='.png'):
    '''
    Make plots for the first paper, which describes the Kepler flare sample.

    The Condor results are aggregated from PostCondor()

    Run on WWU workstation in dir: ~/research/kepler-flares/

    '''

    # read in KIC file
    # http://archive.stsci.edu/pub/kepler/catalogs/ <- data source
    # http://archive.stsci.edu/kepler/kic10/help/quickcol.html <- info

    print(datetime.datetime.now())
    kicdata = pd.read_csv(kicfile, delimiter='|')
    # need KICnumber, gmag, imag, logg (for cutting out crap only)
    # kicnum_k = kicdata['kic_kepler_id']


    fdata = pd.read_table(condorfile, delimiter=',', skiprows=1, header=None)
    ''' KICnumber, lsflag (0=llc,1=slc), dur [days], log(ed68), tot Nflares, sum ED, [ Flares/Day (logEDbin) ] '''

    # need KICnumber, Flare Freq data in units of ED
    kicnum_c = fdata.iloc[:,0].unique()

    print(datetime.datetime.now())
    # total # flares in dataset!
    print('total # flare candidates found: ', fdata.loc[:,4].sum())


    num_fl_tot = fdata.groupby([0])[4].sum()

    plt.figure()
    plt.hist(num_fl_tot.values, bins=100, range=(0,1000), histtype='step', color='k')
    plt.yscale('log')
    plt.xlabel('# Flares per Star')
    plt.ylabel('# Stars')
    plt.savefig(figdir + 'Nflares_hist' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
    # plt.show()
    plt.close()


    ff = open(statsfile, 'w')
    ff.write('This is the stats file for appaloosa.analysis.paper1_plots() \n')

    ff.write('N stars with 25 or more flares: ' + str(len(np.where((num_fl_tot.values >= 25))[0])) + '\n')
    ff.write('Total num flares on stars with 25 or more flares: ' +
             str(np.sum((num_fl_tot.values)[np.where((num_fl_tot.values >= 25))])) + '\n')

    # match two dataframes on KIC number
    # bigdata = pd.merge(kicdata, kicnum_c, how='outer',
    #                    left_on='kic_kepler_id', right_on=0)

    bigdata = kicdata[kicdata['kic_kepler_id'].isin(kicnum_c)]


    # compute the distances and luminosities of all stars
    Lkp_uniq, dist_uniq = energies(bigdata['kic_gmag'],
                                   bigdata['kic_kmag'], return_dist=True)



    # ingest Amy McQuillans rotation period catalog
    rotfile = 'comparison_datasets/Table_Periodic.txt'

    rotdata = pd.read_table(rotfile, delimiter=',', comment='#', header=None)
    # KID,Teff,logg,Mass,Prot,Prot_err,Rper,LPH,w,DC,Flag

    Prot_all = np.zeros(len(kicnum_c)) - 99.


    #########################################
    #      Explanatory Figures
    # including detrending examples, sample LC portions, etc
    # put early in script so can remamke quickly
    print(datetime.datetime.now())


    edbins = np.arange(-5, 5, 0.2)
    edbins = np.append(-10, edbins)
    edbins = np.append(edbins, 10)


    # make FFD plot for specific stars:
    #        GJ 1243, [ R. Clarke     ], J. Cornet,[  A. Boeck     ],  "Pearl"
    s_num = [9726699, 10387822, 10452709, 6224062, 4171937, 12314646, 11551430,
             9349698, 6928206, 5516671, 3222610] # random stars from Walkowicz (2011)


    # For every star: compute flare rate at some arbitrary energy
    Epoint = 35
    EpointS = str(Epoint)

    # set the limit on numbers of flares per star required
    Nflare_limit = 50
    Nflare68_cut = 10

    ##########      THIS IS THE BIG BAD LOOP      ##########

    ap_loop_file = 'ap_analysis_loop.npz'
    print(datetime.datetime.now())

    if rerun is True:
        # silence some fit errors
        warnings.simplefilter('ignore', np.RankWarning)

        Nflare = np.zeros(len(kicnum_c)) # total num flares per star, same as before but slower...
        Nflare68 = np.zeros(len(kicnum_c))

        rate_E = np.zeros(len(kicnum_c)) - 99.
        fit_E = np.zeros(len(kicnum_c)) - 99.
        fit_Eerr = np.zeros(len(kicnum_c)) - 99.

        # vars for L_fl/L_kp (e.g. Lurie 2015)
        dur_all = np.zeros(len(kicnum_c)) - 99. # total duration of the star's LC
        ED_all = np.zeros(len(kicnum_c)) - 99. # sum of all Equiv Dur's for the star

        # Also, compute FFD for every star
        ffd_ab = np.zeros((2,len(kicnum_c)))

        gr_all = np.zeros(len(kicnum_c)) - 99. # color used in prev work
        gi_all = np.zeros(len(kicnum_c)) - 99. # my preferred color

        logg_all = np.zeros(len(kicnum_c)) - 99. # use log g from KIC, with some level of trust

        maxE = np.zeros(len(kicnum_c)) - 99

        meanE = []

        for k in range(len(kicnum_c)):
        # for k in range(199836,199938):

            # find the k'th star in the KIC list in the Flare outputs
            star = np.where((fdata[0].values == kicnum_c[k]))[0]

            Nflare[k] = np.sum(fdata.loc[star,4].values) # total Num of flares
            dur_all[k] = np.sum(fdata.loc[star,2].values) # total duration (units: days)
            ED_all[k] = np.sum(fdata.loc[star,5].values) # total flare energy in Equiv Dur (units: seconds)

            # arrays for FFD
            fnorm = np.zeros_like(edbins[1:])
            fsum = np.zeros_like(edbins[1:])

            # find this star in the KIC data
            mtch = np.where((bigdata['kic_kepler_id'].values == kicnum_c[k]))
            if len(mtch[0])>0:
                gr_all[k] = bigdata['kic_gmag'].values[mtch][0] - \
                            bigdata['kic_rmag'].values[mtch][0]

                gi_all[k] = bigdata['kic_gmag'].values[mtch][0] - \
                            bigdata['kic_imag'].values[mtch][0]

                logg_all[k] = bigdata['kic_logg'].values[mtch][0]

                Lkp_i = Lkp_uniq[mtch][0]

                # for stars listed in the "to plot list", make a FFD figure
                if kicnum_c[k] in s_num:
                    doplot = True
                    plt.figure()
                else:
                    doplot = False

                # tmp array to hold the total number of flares in each FFD bin
                flare_tot = np.zeros_like(fnorm)

                Nflare68tmp = 0 # count number of flares above threshold

                for i in range(0,len(star)):
                    # Find the portion of the FFD that is above the 68% cutoff
                    ok = np.where((edbins[1:] >= fdata.loc[star[i],3]))[0]

                    if len(ok) > 0:
                        # add the rates together for a straight mean
                        fsum[ok] = fsum[ok] + fdata.loc[star[i],6:].values[ok]

                        # count the number for the straight mean
                        fnorm[ok] = fnorm[ok] + 1

                        # add the actual number of flares for this data portion: rate * duration
                        flare_tot = flare_tot + (fdata.loc[star[i],6:].values * fdata.loc[star[i],5])

                        # save the number of flares above E68 for this portion
                        Nflare68tmp = Nflare68tmp + sum((fdata.loc[star[i], 6:].values * fdata.loc[star[i], 5]))

                        if fdata.loc[star[i],1] == 1:
                            pclr = 'red' # long cadence data
                        else:
                            pclr = 'blue' # short cadence data

                        if doplot is True:
                            plt.plot(edbins[1:][ok][::-1] + Lkp_i,
                                     np.cumsum(fdata.loc[star[i],6:].values[ok][::-1]),
                                     alpha=0.35, color=pclr)

                Nflare68[k] = Nflare68tmp

                # the important arrays for the averaged FFD
                ffd_x = edbins[1:][::-1] + Lkp_i
                ffd_y = np.cumsum(fsum[::-1]/fnorm[::-1])

                # the "error" is the Poisson err from the total # flares per bin
                ffd_yerr = _Perror(flare_tot[::-1], down=True) / dur_all[k]

                # Fit the FFD w/ a line, save the coefficeints
                ffd_ok = np.where((ffd_y > 0) & np.isfinite(ffd_y) &
                                  np.isfinite(ffd_x) & np.isfinite(ffd_yerr))

                # if there are any valid bins, find the max energy (bin)
                if len(ffd_ok[0])>0:
                    maxE[k] = np.nanmax(ffd_x[ffd_ok])

                # if there are at least 2 energy bins w/ valid flares...
                if len(ffd_ok[0])>1:
                    # compute the mean flare energy (bin) for this star
                    meanE = np.append(meanE, np.nanmedian(ffd_x[ffd_ok]))

                    '''
                    # the weights, in log rate units
                    ffd_weights = 1. / np.abs(ffd_yerr[ffd_ok]/(ffd_y[ffd_ok] * np.log(10)))

                    # fit the FFD w/ a line
                    fit, cov = np.polyfit(ffd_x[ffd_ok], np.log10(ffd_y[ffd_ok]), 1, cov=True, w=ffd_weights) # fit using weights

                    # evaluate the FFD fit at the Energy point
                    fit_E[k] = 10.**(np.polyval(fit, Epoint))
                    '''

                    p0 = [-0.5, np.log10(np.nanmax(ffd_y[ffd_ok]))]
                    # fit, cov = curve_fit(_plaw, ffd_x[ffd_ok], ffd_y[ffd_ok], sigma=ffd_yerr[ffd_ok],
                    #                      absolute_sigma=False, p0=p0)
                    # fit_E[k] = _plaw(Epoint, *fit)


                    fit, cov = curve_fit(_linfunc, ffd_x[ffd_ok], np.log10(ffd_y[ffd_ok]), p0=p0,
                                         sigma=np.abs(ffd_yerr[ffd_ok]/(ffd_y[ffd_ok] * np.log(10))) )

                    fit_E[k] = 10.0**_linfunc(Epoint, *fit)

                    ffd_ab[:,k] = fit


                    # determine uncertainty on the fit evaluation point, with help from:
                    # http://stackoverflow.com/questions/28505008/numpy-polyfit-how-to-get-1-sigma-uncertainty-around-the-estimated-curve
                    TT = np.vstack([Epoint**(1-i) for i in range(2)]).T
                    # yi = np.dot(TT, fit)  # matrix multiplication calculates the polynomial values
                    C_yi = np.dot(TT, np.dot(cov, TT.T)) # C_y = TT*C_z*TT.T
                    fit_Eerr[k] = np.sqrt(np.diag(C_yi))  # Standard deviations are sqrt of diagonal


                # determine the actual value of the FFD at the Energy point using the fit
                # if (sum(ffd_x >= Epoint) > 0):
                #     rate_E[k] = max(ffd_y[ffd_x >= Epoint])

                if doplot is True:
                    print(kicnum_c[k])
                    print('ffd_ok:', ffd_ok)
                    print('ffd_x:', ffd_x)
                    print('ffd_y:', ffd_y)
                    print('ffd_yerr:', ffd_yerr)
                    # print('meanE:', meanE)

                    plt.plot(ffd_x, ffd_y, linewidth=2, color='black', alpha=0.7)
                    plt.errorbar(ffd_x, ffd_y, ffd_yerr, fmt='k,')
                    if len(ffd_ok[0])>1:
                        print('FIT: ', fit)

                        # plt.plot(ffd_x[ffd_ok], 10.0**(np.polyval(fit, ffd_x[ffd_ok])),
                        #          color='orange', linewidth=4, alpha=0.5)

                        # plt.plot(ffd_x[ffd_ok], _plaw(ffd_x[ffd_ok], *fit),
                        #          color='orange', linewidth=4, alpha=0.5)

                        plt.plot(ffd_x[ffd_ok], 10.0**_linfunc(ffd_x[ffd_ok], *fit),
                                 color='orange', linewidth=4, alpha=0.5)


                        plt.yscale('log')
                        plt.xlim(np.nanmin(ffd_x[ffd_ok])-0.5, np.nanmax(ffd_x[ffd_ok])+0.5)
                        # plt.ylim(1e-3, 3e0)

                    # plt.title('KIC' + str(kicnum_c[k]) + ': ' +
                    #           'log R$_{'+EpointS+'}$ = ' + str(np.log10(fit_E[k])))
                    plt.xlabel('log Flare Energy (erg)')
                    plt.ylabel('Cumulative Flare Freq (#/day)')

                    plt.savefig(figdir + str(kicnum_c[k]) + '_ffd' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
                    plt.close()



            # now match this star to the rotation period data
            rotmtch = np.where(rotdata.iloc[:,0].values == kicnum_c[k])
            if len(rotmtch[0])>0:
                Prot_all[k] = rotdata.iloc[:,4].values[rotmtch]

        # save results for faster reuse
        np.savez(ap_loop_file,
                 Nflare=Nflare, Nflare68=Nflare68, rate_E=rate_E, fit_E=fit_E, fit_Eerr=fit_Eerr,
                 ffd_ab=ffd_ab, gr_all=gr_all, gi_all=gi_all, meanE=meanE, maxE=maxE,
                 Prot_all=Prot_all, ED_all=ED_all, dur_all=dur_all, logg_all=logg_all)

        ##### END OF THE BIG BAD LOOP #####

    else:
        # pull arrays back in via load!
        npz = np.load(ap_loop_file)
        Nflare = npz['Nflare']
        rate_E = npz['rate_E']
        fit_E = npz['fit_E']
        fit_Eerr = npz['fit_Eerr']
        ffd_ab = npz['ffd_ab']
        gr_all = npz['gr_all']
        gi_all = npz['gi_all']
        meanE = npz['meanE']
        maxE = npz['maxE']
        Prot_all = npz['Prot_all']
        dur_all = npz['dur_all']
        ED_all = npz['ED_all']
        logg_all = npz['logg_all']
        Nflare68 = npz['Nflare68']
    print(datetime.datetime.now())


    #### a histogram of the average flare energy per star
    plt.figure()
    _htmp = plt.hist(meanE[np.where(np.isfinite(meanE))], bins=50)
    plt.xlabel('mean energy (log E)')
    plt.ylabel('# stars')
    plt.savefig(figdir + 'mean_energy' + figtype,dpi=100)
    plt.close()



    ### plot of maxE vs color
    Eok = np.where((maxE > 0))

    plt.figure()
    plt.scatter(gi_all[Eok], maxE[Eok], alpha=0.5, linewidths=0)
    plt.xlabel('g-i (mag)')
    plt.ylabel('Max log Flare Energy (erg)')
    plt.xlim(-1,3)
    plt.ylim(28,40)
    plt.savefig(figdir + 'maxE_vs_gi' + figtype, dpi=100)
    plt.close()

    ### histogram of maxE
    plt.figure()
    _ = plt.hist(maxE[Eok], bins=50)
    plt.xlabel('Max log Flare Energy (erg)')
    plt.ylabel('# stars')
    plt.savefig(figdir + 'logE_hist' + figtype, dpi=100)
    plt.close()


    ############################
    # the big master plot, style taken from the K2 meeting plot...
    # plots vs R35
    if False:
        clr = np.log10(fit_E)
        clr_raw = clr

        clr_raw_err = np.abs(fit_Eerr / (fit_E * np.log(10)))

        ff.write(str(len((np.where(np.isfinite(clr)))[0])) + ' stars have valid R_' + EpointS + ' values \n')

        isF = np.where(np.isfinite(clr))

        clr_rng = np.array([-2., 2.] )* np.nanstd(clr) + np.nanmedian(clr)


        ff.write('Nflare_limit = ' + str(Nflare_limit) + '\n')
        ff.write('# flares on stars that pass this limit: ' +
                 str(np.sum(Nflare[np.where((Nflare >= Nflare_limit))])) + '\n')
        ff.write('# stars that pass this limit: ' +
                 str(len(np.where((Nflare >= Nflare_limit))[0])) + '\n')

        ff.write('Nflare68_limit = ' + str(Nflare68_cut) + '\n')
        ff.write('# flares on stars that pass this limit: ' +
                 str(np.sum(Nflare[np.where((Nflare68 >= Nflare68_cut))])) + '\n')
        ff.write('# stars that pass this limit: ' +
                 str(len(np.where((Nflare68 >= Nflare68_cut))[0])) + '\n')


        # stars that have enough flares and have valid rates
        okclr = np.where((Nflare68 >= Nflare68_cut) & #(logg_all >= 3.8) &
                         np.isfinite(clr) & (Nflare >= Nflare_limit))

        # stars that just have valid rates
        okclr0 = np.where(  # (clr >= clr_rng[0]) & (clr <= clr_rng[1]) &
            np.isfinite(clr) & (Nflare >= 0))



        plt.figure()
        hh = plt.hist(clr[isF], bins=100, histtype='step', color='k')
        plt.xlabel('log R$_{'+EpointS+'}$ (#/day)')
        plt.ylabel('# Stars')
        plt.yscale('log')
        plt.savefig(figdir + 'R_' + EpointS + '_hist' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
        plt.close()



        # lets breifly revisit Nflares, look at where to pick a limit
        plt.figure()
        _ = plt.hist(np.log10(Nflare + 0.01), bins=100, cumulative=True, normed=True,
                     histtype='step', color='k')
        plt.xlim(-1,3)

        plt.axvline(x=np.log10(Nflare_limit), linewidth=3, color='red', alpha=0.5)
        plt.xlabel('log # Flares per Star')
        plt.ylabel('Cumulative Fraction of Stars')
        plt.savefig(figdir + 'cumulative_hist' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
        plt.close()



        ff.write('okclr len is ' + str(len(okclr[0])) + '\n')
        ff.write('okclr0 len is ' + str(len(okclr0[0])) + '\n')

        # ff.write('# stars that pass Nflare_limit and have valid rotation periods: '+
        #          str( len(np.where((Nflare >= Nflare_limit) & (Prot_all > 0.1))[0]) ) + '\n')
        print(datetime.datetime.now())



        # first, a basic plot of flare rate versus color

        rate_range = [[0,3], [10.**clr_rng[0], 10.**clr_rng[1]]]

        plt.figure()
        plt.hist2d(gi_all[okclr], fit_E[okclr], bins=100, range=rate_range,
                   alpha=1.0, norm=LogNorm(), cmap=cm.Greys)
        plt.xlabel('g-i (mag)')
        plt.yscale('log')
        plt.ylabel('R$_{'+EpointS+'}$ (#/day)')
        plt.savefig(figdir + 'flarerate_okclr' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
        plt.close()

        plt.figure()
        plt.hist2d(gi_all[okclr0], fit_E[okclr0], bins=100, range=rate_range,
                   alpha=1.0, norm=LogNorm(), cmap=cm.Greys)
        plt.xlabel('g-i (mag)')
        plt.yscale('log')
        plt.ylabel('R$_{'+EpointS+'}$ (#/day)')
        plt.savefig(figdir + 'flarerate_okclr0' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
        plt.close()


        ##### The science plot! #####
        ##### try it as a scatter plot


        ####    do it again, but now with (g-i) color   ###
        plt.figure()
        plt.scatter(gi_all[okclr], Prot_all[okclr], c=clr[okclr],
                    alpha=0.7, lw=0.5, cmap=cm.afmhot_r, s=50)
        plt.xlabel('g-i (mag)')
        plt.ylabel('P$_{rot}$ (days)')
        plt.yscale('log')
        plt.xlim((0,3))
        plt.ylim((0.1,100))
        cb = plt.colorbar()
        cb.set_label('log R$_{'+EpointS+'}$ (#/day)')
        plt.savefig(figdir + 'masterplot_okclr_gi' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
        plt.close()

        ####
        plt.figure()
        plt.scatter(gi_all[okclr0], Prot_all[okclr0], c=clr[okclr0],
                    alpha=0.7, lw=0.5, cmap=cm.afmhot_r, s=50)
        plt.xlabel('g-i (mag)')
        plt.ylabel('P$_{rot}$ (days)')
        plt.yscale('log')
        plt.xlim((0,3))
        plt.ylim((0.1,100))
        cb = plt.colorbar()
        cb.set_label('log R$_{'+EpointS+'}$ (#/day)')
        plt.savefig(figdir + 'masterplot_okclr0_gi' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
        plt.close()


        ################
        # pick target star color range, look at evolution of Rate vs Rotation

        crng = np.array([[0.5, 0.75],[0.75, 1.],[1.50, 2.],[2.25, 2.75]])

        for k in range(crng.shape[0]):
            ts = np.where((gi_all[okclr]  >= crng[k,0]) &
                          (gi_all[okclr] <= crng[k,1]) &
                          (Prot_all[okclr] > 0.1))

            ff.write('# that pass TS color cut: '+str(len(ts[0])) + '\n')

            plt.figure()
            # plt.scatter(Prot_all[okclr0][ts0], clr_raw[okclr0][ts0], s=20, alpha=0.7,lw=0.5,c='red')
            plt.scatter(Prot_all[okclr][ts], clr_raw[okclr][ts], s=50, alpha=1,lw=0.5, c='k')
            # plt.errorbar(Prot_all[okclr][ts], clr_raw[okclr][ts], yerr=clr_raw_err[okclr][ts], fmt='k,')
            plt.xlabel('P$_{rot}$ (days)')
            plt.ylabel('log R$_{'+EpointS+'}$ (#/day)')
            plt.title(str(crng[k,0])+' < (g-i) < '+str(crng[k,1]))
            plt.xscale('log')
            plt.ylim(-4,0)
            plt.xlim(0.1,100)
            plt.savefig(figdir + 'rot_rate'+str(k) + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
            plt.close()


    ##### make master (color,rot,rate) figure as a pixelated plot
    '''
    bin2d, xx, yy, _ = binned_statistic_2d(gr_all[okclr], np.log10(Prot_all[okclr]), clr[okclr],
                                           statistic='median', range=[[-1,4],[-1,2]], bins=75)

    plt.figure()

    plt.imshow(bin2d.T, interpolation='nearest', aspect='auto', origin='lower',
               extent=(xx.min(),xx.max(),yy.min(),yy.max()),
               cmap=plt.cm.afmhot_r)

    plt.xlabel('g-r (mag)')
    plt.ylabel('log P$_{rot}$ (days)')
    plt.xlim((0,1.7))
    plt.ylim(-1,2)
    cb = plt.colorbar()
    cb.set_label('log R$_{'+EpointS+'}$ (#/day)')
    plt.savefig('masterplot_pixel.png', dpi=300, bbox_inches='tight', pad_inches=0.5)
    plt.close()
    '''


    #########################################
    #########################################
    #    plots as a function of Lfl_Lbol

    # total fractional energy (in seconds) / total duration (in seconds)
    Lfl_Lbol = ED_all / (dur_all * 60. * 60. * 24.)

    Lfl_Lbol_label = 'log ($L_{fl}$ $L_{Kp}^{-1}$)'

    # spit out table of KID, color (g-i), Lfl/Lbol
    dfout = pd.DataFrame(data={'kicnum':kicnum_c,
                               'giclr':gi_all,
                               'LflLbol':Lfl_Lbol})
    dfout.to_csv('kic_lflare.csv')



    clr = np.log10(Lfl_Lbol)
    clr_raw = clr
    isF = np.where(np.isfinite(clr))

    # clr_rng = np.array([-3., 3.] )* np.nanstd(clr[isF]) + np.nanmedian(clr[isF])


    ## clip data at max/min range
    # clr[np.where((clr < clr_rng[0]) & np.isfinite(clr))] = clr_rng[0]
    # clr[np.where((clr > clr_rng[1]) & np.isfinite(clr))] = clr_rng[1]

    okclr = np.where((Nflare68 >= Nflare68_cut) & #(logg_all >= 3.5) &
                     np.isfinite(clr) & (Nflare >= Nflare_limit))

    ff.write('OKCLR rules: Lfl/Lkp>0, Nflare>'+str(Nflare_limit)+', Nflare68>'+str(Nflare68_cut)+'\n')
    ff.write('# stars that pass final "OKCLR" cuts: ' + str(len(okclr[0])) + '\n')
    ff.write('# flares on stars that pass final OKCLR cut: ' + str(np.sum(Nflare[okclr])) + '\n')
    ff.write('# stars that pass OKCLR cut, and have Prot>0.1: ' +
             str(len(np.where(Prot_all[okclr] > 0.1)[0]))+'\n')

    plt.figure()
    plt.scatter(gi_all, Prot_all, c=clr_raw,
                alpha=0.7, lw=0.5, cmap=cm.afmhot_r, s=25)
    plt.xlabel('g-i (mag)')
    plt.ylabel('P$_{rot}$ (days)')
    plt.yscale('log')
    plt.xlim((0,3))
    plt.ylim((0.1,100))
    cb = plt.colorbar()
    cb.set_label(Lfl_Lbol_label)
    plt.savefig(figdir + 'masterplot_lfl_lkep_raw' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
    plt.close()


    plt.figure()
    plt.scatter(gi_all[okclr], Prot_all[okclr], c=clr[okclr],
                alpha=0.7, lw=0.5, cmap=cm.afmhot_r, s=50)
    plt.xlabel('g-i (mag)')
    plt.ylabel('P$_{rot}$ (days)')
    plt.yscale('log')
    plt.xlim((0,3))
    plt.ylim((0.1,100))
    cb = plt.colorbar()
    cb.set_label(Lfl_Lbol_label)
    plt.savefig(figdir + 'masterplot_lfl_lkep' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
    plt.close()


    ### plot of Nflares vs color
    plt.figure()
    plt.scatter(gi_all[okclr], Nflare[okclr], alpha=0.5, linewidths=0, c='k')
    plt.xlabel('g-i (mag)')
    plt.ylabel('Number of Flares')
    plt.yscale('log')
    plt.ylim(0.9e2,1e5)
    plt.xlim(-1,3)
    plt.savefig(figdir + 'Nflare_vs_gi' + figtype, dpi=100)
    plt.close()

    plt.figure()
    plt.scatter(gi_all[okclr], Nflare68[okclr], alpha=0.5, linewidths=0, c='k')
    plt.xlabel('g-i (mag)')
    plt.ylabel('Number of Flares (E > E$_{68}$)')
    plt.yscale('log')
    plt.ylim(0.9e2,1e5)
    plt.xlim(-1,3)
    plt.savefig(figdir + 'Nflare_vs_gi' + figtype, dpi=100)
    plt.close()


    plt.figure()
    plt.scatter(gi_all[isF], Nflare[isF], alpha=0.5, linewidths=0, c='k')
    plt.xlabel('g-i (mag)')
    plt.ylabel('Number of Flares')
    plt.yscale('log')
    plt.ylim(0.9e2,1e5)
    plt.xlim(-1,3)
    plt.savefig(figdir + 'Nflare_vs_gi_raw' + figtype, dpi=100)
    plt.close()

    plt.figure()
    _ = plt.hist(Nflare68[okclr], bins=100, histtype='step', color='k')
    plt.xlabel('Number of Flares per Star (E > E$_{68}$)')
    plt.ylabel('Number of Stars')
    plt.yscale('log')
    plt.savefig(figdir + 'Nflare68' + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
    plt.close()

    crng = np.array([[0.5, 1.0],
                     [1., 1.5],
                     [1.5, 2.],
                     [2., 2.5],
                     [2.5, 3.]])

    for k in range(crng.shape[0]):
        ts = np.where((gi_all[okclr]  > crng[k,0]) &
                      (gi_all[okclr] <= crng[k,1]) &
                      Prot_all[okclr] > 0.1)

        ff.write('# that pass color cut: '+str(len(ts[0])) + '\n')

        plt.figure()
        # plt.scatter(Prot_all[okclr0][ts0], clr_raw[okclr0][ts0], s=20, alpha=0.7,lw=0.5,c='red')
        plt.scatter(Prot_all[okclr][ts], clr_raw[okclr][ts], s=50, alpha=1,lw=0.5, c='k')
        # plt.errorbar(Prot_all[okclr][ts], clr_raw[okclr][ts], yerr=clr_raw_err[okclr][ts], fmt='k,')
        plt.xlabel('P$_{rot}$ (days)')
        plt.ylabel(Lfl_Lbol_label)
        plt.title(str(crng[k,0])+' < (g-i) < '+str(crng[k,1]))
        plt.xscale('log')
        plt.ylim(-6,-1)
        plt.xlim(0.1,100)
        plt.savefig(figdir + 'rot_lfllkp'+str(k) + figtype, dpi=300, bbox_inches='tight', pad_inches=0.5)
        plt.close()


    #    / plots as a function of Lfl_Lbol
    #########################################


    #########################################
    #      NGC 6811 plots



    ocfile='comparison_datasets/meibom2011_tbl1.txt'

    # Remake the gyrochronology plot from Meibom et al (2011) for NGC 6811 (color vs Prot),
    #  and add another panel of (color vs flare rate) or something similar

    ocdata = pd.read_table(ocfile, header=None, comment='#', delim_whitespace=True)
    # col's I care about:
    # KIC=0, g=7, r=8, Per=9


    ##### simple rotation period plot remake from paper
    plt.figure()
    plt.scatter((ocdata.iloc[:,7]-ocdata.iloc[:,8]), ocdata.iloc[:,9])
    plt.xlabel('g-r (mag)')
    plt.ylabel('P$_{rot}$ (days)')
    plt.savefig(figdir + 'ngc6811_gyro.png', dpi=300, bbox_inches='tight', pad_inches=0.5)
    # plt.show()
    plt.close()

    rate_oc = np.zeros(ocdata.shape[0]) - 99.
    fit_oc = np.zeros(ocdata.shape[0]) - 99.
    Lfl_Lbol_oc = np.zeros(ocdata.shape[0]) - 99.

    for k in range(ocdata.shape[0]):
        mtch = np.where((kicnum_c == ocdata.iloc[:,0].values[k]))
        if len(mtch[0])>0:
            rate_oc[k] = rate_E[mtch]
            fit_oc[k] = np.polyval(ffd_ab[:,mtch], Epoint)
            Lfl_Lbol_oc[k] = clr_raw[mtch]


    '''
    #####
    plt.figure()
     # add contours for the entire field
    # plt.hist2d(gr_all[okclr], fit_E[okclr], bins=100, range=rate_range,
    #            alpha=1.0, norm=LogNorm(), cmap=cm.Greys)
    plt.scatter((ocdata.iloc[:,7]-ocdata.iloc[:,8]), fit_oc)
    plt.xlabel('g-r (mag)')
    plt.xlim(0.2, 0.9)
    plt.ylim(-3.5, -2)
    plt.ylabel('R$_{'+EpointS+'}$ (#/day)')
    plt.savefig('ngc6811_flare_all.png', dpi=300, bbox_inches='tight', pad_inches=0.5)
    plt.close()



    #####

    plt.figure()
    plt.scatter(gr_all[okclr], Prot_all[okclr], c=clr[okclr], alpha=0.7, lw=0, cmap=cm.afmhot_r, s=50)
    cb = plt.colorbar()
    cb.set_label('log R$_{'+EpointS+'}$ (#/day)')
    plt.scatter((ocdata.iloc[:,7]-ocdata.iloc[:,8]), ocdata.iloc[:,9], c=np.log10(fit_oc), cmap=cm.YlGnBu_r, s=50)
    plt.xlabel('g-r (mag)')
    plt.ylabel('P$_{rot}$ (days)')
    plt.yscale('log')
    plt.xlim((0,1.7))
    plt.ylim((0.1,100))
    cb2 = plt.colorbar()
    plt.savefig('masterplot_cluster.png', dpi=300, bbox_inches='tight', pad_inches=0.5)
    plt.close()
    # plt.show()
    '''

    ####
    plt.figure()
    plt.scatter((ocdata.iloc[:, 7] - ocdata.iloc[:, 8]), Lfl_Lbol_oc, s=50)
    plt.xlabel('g-r (mag)')
    plt.ylabel(Lfl_Lbol_label)
    plt.ylim(-7, 1)
    # plt.xlim(0, 1.7)
    plt.savefig(figdir + 'ngc6811_Lfl.png', dpi=300, bbox_inches='tight', pad_inches=0.5)
    plt.close()


    #      /NGC 6811 plots
    #########################################




    ### stars with 50 largest E flares
    Esort = np.argsort(maxE)[::-1]

    Efair = np.where((maxE[Esort] < 40))

    ff.write('__ top 50 energy flare stars __' + '\n')
    for k in range(0, 50):
        ff.write(str(kicnum_c[Esort][Efair][k]) +
                 ', ' + str(maxE[Esort][Efair][k]) + '\n')


    ff.close() # close the output stats file
    return


# def energies(gmag, rmag, imag, isochrone='1.0gyr.dat', return_dist=False):
def energies(gmag, kmag, isochrone='1.0gyr.dat', return_dist=False):
    '''
    Compute the quiescent energy for every star. Use the KIC (g-i) color,
    with an isochrone, get the absolute Kepler mag for each star, and thus
    the distance & luminosity.

    Isochrone is a 0.5 Gyr track from the Padova CMD v2.7
    http://stev.oapd.inaf.it/cgi-bin/cmd_2.7

    Kepler and Sloan phot system both in AB mags.

    Returns
    -------
    Quiescent Luminosities in the Kepler band
    '''

    # read in Padova isochrone file
    # note, I've cheated and clipped this isochrone to only have the
    # Main Sequence, up to the blue Turn-Off limit.

    try:
        __file__
    except NameError:
        __file__ = os.getenv("HOME") +  '/python/appaloosa/analysis.py'

    dir = os.path.dirname(os.path.realpath(__file__)) + '/misc/'

    '''
    Mkp, Mg, Mr, Mi = np.loadtxt(dir + isochrone, comments='#',
                                 unpack=True, usecols=(8,9,10,11))

    # To match observed data to the isochrone, cheat:
    # e.g. Find interpolated g, given g-i. Same for Kp

    # do this 3 times, each color combo. Average result for M_kp
    Mgi = (Mg-Mi)
    ss = np.argsort(Mgi) # needs to be sorted for interpolation
    Mkp_go = np.interp((gmag-imag), Mgi[ss], Mkp[ss])
    Mg_o = np.interp((gmag-imag), Mgi[ss], Mg[ss])

    Mgr = (Mg-Mr)
    ss = np.argsort(Mgr)
    Mkp_ro = np.interp((gmag-rmag), Mgr[ss], Mkp[ss])
    Mr_o = np.interp((gmag-rmag), Mgr[ss], Mr[ss])

    Mri = (Mr-Mi)
    ss = np.argsort(Mri)
    Mkp_io = np.interp((rmag-imag), Mri[ss], Mkp[ss])
    Mi_o = np.interp((rmag-imag), Mri[ss], Mi[ss])

    Mkp_o = (Mkp_go + Mkp_ro + Mkp_io) / 3.0

    dist_g = np.array(_DistModulus(gmag, Mg_o), dtype='float')
    dist_r = np.array(_DistModulus(rmag, Mr_o), dtype='float')
    dist_i = np.array(_DistModulus(imag, Mi_o), dtype='float')
    dist = (dist_g + dist_r + dist_i) / 3.0

    dm_g = (gmag - Mg_o)
    dm_r = (rmag - Mr_o)
    dm_i = (imag - Mi_o)
    dm = (dm_g + dm_r + dm_i) / 3.0
    '''


    Mkp, Mg, Mk = np.loadtxt(dir + isochrone, comments='#',
                             unpack=True, usecols=(8,9,18))

    Mgk = (Mg-Mk)
    ss = np.argsort(Mgk) # needs to be sorted for interpolation
    Mkp_o = np.interp((gmag-kmag), Mgk[ss], Mkp[ss])
    Mk_o = np.interp((gmag-kmag), Mgk[ss], Mk[ss])

    dist = np.array(_DistModulus(kmag, Mk_o), dtype='float')
    dm = (kmag - Mk_o)

    pc2cm = 3.08568025e18

    # returns Flux [erg/s/cm^2]
    F_kp = _ABmag2flux(Mkp_o + dm)

    # again, classic bread/butter right here,
    # change Flux to Luminosity [erg/s]
    L_kp = np.array(F_kp * (4.0 * np.pi * (dist * pc2cm)**2.0), dtype='float')

    # !! Should be able to include errors on (g-i), propogate to
    #    errors on Distance, and thus lower error limit on L_kp !!

    # !! Should have some confidence about the interpolation,
    #    e.g. if beyond g-i isochrone range !!

    if return_dist is True:
        return np.log10(L_kp), dist
    else:
        return np.log10(L_kp)


'''
  let this file be called from the terminal directly. e.g.:
  $ python analysis.py
'''
if __name__ == "__main__":
    # import sys
    paper1_plots()
