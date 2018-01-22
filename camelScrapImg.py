
class camelScrap(object):
    def __init__(self, fname, alpha = 1.5):
        if os.path.exists(fname):
            self.im = Image.open(fname)
            self.fname = fname
            self.asin = fname[-14:-4]
            _im1 = self.im.crop((0,455,970,470))
            _im1 = ImageEnhance.Contrast(_im1)
            _im1 = _im1.enhance(alpha)
            self.timeStrip = _im1
            self.isempty = (np.array(self.timeStrip)<255).sum()<100
            self._boxes = ''
            self._t1 = 0
            self._t2 = 0
            self._Scale = None
            self.label = None
            self.y_zero = None
            self.extracted_new = None
            self.factor= 2
            self.x_end = 0
            
        else:
            print 'wrong filename, obejct was not created'
    def __str__(self):
        return 'member of camelScrap: ASIN %s, dimensions %d x %d' %(self.asin, self.im.width, self.im.height)
    def __repr__(self):
        return 'member of camelScrap: ASIN %s' %(self.asin)
    
    def show(self, scale=0.1):
        plt.figure(figsize=(20,10))
        plt.imshow(self.im)
    

    def OCR_time(self, factor = 2):
        self.factor = factor
        im_ = self.timeStrip
        im_ = im_.resize(( im_.width * factor,im_.height * factor),Image.BICUBIC)
        self.years = pytesseract.image_to_string(im_,  boxes=False, config = '--psm 7 -c tessedit_char_whitelist=0123456789') 
        self._boxes = pytesseract.image_to_string(im_,  boxes=True, config = '--psm 7 -c tessedit_char_whitelist=0123456789')
        
        return self.years
    def setCoordinates(self):
        if self._boxes =='': self.OCR_time()            
        boxes = self._boxes
        factor = self.factor
        a = np.array([a.split(' ') for a in boxes.split('\n')])
        s = ''.join(a[:,0])
        if len(s)>16:
            ##calculate last recorded full year range (so not the padding years) 
            year_begin = int(s[4:8])
            year_end = 2017

            _ind = s.find(str(year_end))

            if year_end != year_begin + (1.*_ind/4-1):
                print 'end year does not match'

        #             if self.years.split()[-4:-1] !=['2015','2016', '2017']: ## same as
                if s[_ind-4:_ind] == str(year_end-1) and s[_ind-8:_ind-4] == str(year_end-2):
                    year_begin = year_end -(_ind/4-1)
                else:
                    print "failed twice !"
                    print '2016 is',s[_ind-4:_ind] == str(year_end-1) , '2015 is',s[_ind-8:_ind-4] == str(year_end-2)


            # x1 = 1.*a[4,1]/factor
            x_begin = float(a[4,1])/factor

            x_end = float(a[_ind,1])/factor
            self.x_end = x_end

            t2 = int(datetime.datetime(year_end,01,01).strftime("%s"))
            t1 = int(datetime.datetime(year_begin,01,01).strftime("%s"))
            Scale = 1.0*(t2-t1)/(x_end-x_begin)
            self._t1 = t1
            self._t2 = t2
            self._Scale = Scale
        else:
            self._Scale = 0
            print 'Only very recent data!'
        
    def getTime(self,pixel):
        if self._Scale ==None: self.setCoordinates()
        t1,t2,Scale = self._t1,self._t2, self._Scale
        t = t2 + int((pixel - self.x_end)*Scale)
        t_datetime = datetime.date.fromtimestamp(t)
        return t, t_datetime
    
    def find_zero(self):
        ## returns estimated y-coordinate for y==0(in pixels from the left top corner) 
        ## it does that by searching for a dark grey line that is persistent across all image

        if self.isempty: return
        ima = np.array(self.im)
        
        Ydim, Xdim = ima.shape[:2]
        foo = [np.where(np.all(ima[:,col,:2]==75, axis=1))[0] for col in range(Xdim)]
        foo = [[n,i.mean()] for n,i in enumerate(foo) if  len(i)]
        foo = np.array(foo)
        y_zero = int(np.median(foo))
        self.y_zero = y_zero
        return y_zero
    def find_new(self):
        ima = np.array(self.im)
        Ydim, Xdim = ima.shape[:2]
        if self.y_zero is None: self.find_zero()
        y_zero = self.y_zero
        foo = [np.where((ima[:y_zero,col,0]<10)&(ima[:y_zero,col,2]>150))[0] for col in range(Xdim)]
        foo = [[n, y_zero - i.mean()] for n,i in enumerate(foo) if  len(i)]
        extracted_new = np.array(foo)  
        extracted_new[:,0] = [self.getTime(pixel)[0] for pixel in extracted_new[:,0]]
        self.extracted_new = extracted_new
        return extracted_new
    def OCR_getLabel(self):
        im = self.im.crop((45,0,545,16)).resize((1000,30), Image.BILINEAR)
        self.label = pytesseract.image_to_string(im,  boxes=False, lang = 'eng', config = r'--psm 7 -c tessedit_char_blacklist=\\//')
        
    def populate(self):
        if  self.isempty: 
            print 'Seem like there is no plot'
            return
        if self.label is None:
            self.OCR_getLabel()
        if self.extracted_new is None:
            self.find_new()
        
def UtoD(i):
#     Just to remmeber hpw to go from Unix timestamp to date object and back
    return datetime.datetime.fromtimestamp(i)
def DtoU(i):
#     Just to remmeber hpw to go from Unix timestamp to date object and back
    return int(i.strftime('%s'))