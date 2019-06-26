#!/usr/bin/env python3.7
# encoding: utf-8
'''
stegi -- stegsolve as cli

@author:     localo
'''

from PIL import Image,ImageFile
import numpy as np
ImageFile.LOAD_TRUNCATED_IMAGES = True
import sys
import os
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2019-06-19'
__updated__ = '2019-06-19'

DEBUG = 0

def get_channel_bits(arr,channel_mask, plane_mask,keep_color):
    if arr.ndim != 3:
        print("Invalid dim")
        return arr
    (_,_,c) = arr.shape
    if channel_mask.bit_length()>c:
        print("Invalid channel mask")
        return arr    
    for n in range(c):
        arr[:,:,n] = np.bitwise_and(arr[:,:,n],plane_mask if ((1<<n)&channel_mask) != 0 else 0)*255
    if not keep_color:
        f_arr = np.tile(0, c)
        t_arr = np.tile(255, c)
        mask = (arr ==f_arr).all(axis=2)
        arr[~mask]=t_arr
    return arr

def process_one(arr,keep_color,out_file,raw_binary,col):
    (_,_,c) = arr.shape
    if raw_binary:
        if not keep_color:
            f_arr = np.tile(0, c)
            mask = (arr == f_arr).all(axis=2)
        else:
            mask = (arr[:,:,:]==0)
        data = np.packbits((~mask).flatten('F' if col else 'C')).tobytes()
        if out_file:
            with open(out_file,"wb") as f:
                f.write(data)
        else:
            sys.stdout.buffer.write(data)
    else: 
        new_img = Image.fromarray(arr, 'RGB')                
        if not out_file:
            new_img.show()
        else:
            new_img.save(out_file)

def process(filename,channel_mask=0b0,plane_mask=0b1,keep_color=False,out_file=False,all_masks=False,raw_binary=False,col=False):
    with Image.open(filename) as img:
        arr = np.array(img)
        (_,_,c) = arr.shape
        if not all_masks:   
            new_arr = get_channel_bits(arr,channel_mask,plane_mask,keep_color)
            process_one(new_arr,keep_color,out_file,raw_binary,col)
        else:
            os.makedirs(out_file,exist_ok=True)
            for n in range(c+1):
                for i in range(8):
                    new_arr = get_channel_bits(np.copy(arr),1<<n if n< c else (1<<n)-1,1<<i,keep_color)
                    filename = "%s/%s"%(out_file,"{0}_{1:08b}.{2}".format(n,1<<i,"bin" if raw_binary else "bmp")) 
                    process_one(new_arr,keep_color,filename,raw_binary,col)
                    print("\rDone: %d/%d"%(i+n*8+1,(c+1)*8),end="")
    return 0
    

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_shortdesc, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-b', nargs='?',  dest="plane_mask", help='plane bit mask')
        parser.add_argument('-c', nargs='?',  dest="channel_mask", help='channel bit mask')
        parser.add_argument('-k',  dest="keep_color", help='keep the original color',action='store_true')
        parser.add_argument('-o',  nargs='?',dest="out_file", help='output file')
        parser.add_argument('-a', dest="all", help='output all',action='store_true')
        parser.add_argument('-r', dest="raw", help='to raw binary data',action='store_true')
        parser.add_argument('--column', dest="column", help='raw binary decode column',action='store_true')
        
        
        parser.add_argument(dest="input", help="input file", metavar="file")
        
        # Process arguments
        args = parser.parse_args()
        
        file = args.input
        verbose = args.verbose
        
        channel_mask = 0b0 if not args.channel_mask else int(args.channel_mask,2)
        plane_mask = 0b0 if not args.plane_mask else int(args.plane_mask,2)
        keep_color = args.keep_color
        out_file = "out" if not args.out_file and args.all else args.out_file
        all_masks = args.all
        raw_binary = args.raw
        column = args.column

        if verbose and verbose > 0:
            print("Verbose: %r"%(verbose))
            print("File: %s" %(file))
            print("Channel mask: {0:b}".format(channel_mask))
            print("Plane mask: {0:b}".format(plane_mask))
            print("Keep color: %r" % (keep_color))
            print("Output file: %s" % (out_file))
            print("All masks: %r" % (all_masks))
        if not file:
            print("Please specify a file")
            return 1 
        return process(file,channel_mask,plane_mask,keep_color,out_file,all_masks,raw_binary,column)
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        if DEBUG:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
        sys.argv.append("-c 001")
        sys.argv.append("-b 1")
        sys.argv.append("-k")
        sys.argv.append("-r")
        sys.argv.append("-o out")
        sys.argv.append("test.jpg")
    sys.exit(main())
