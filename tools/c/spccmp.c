#include <stdint.h>
#include <stdlib.h>
#include <string.h>
static uint8_t BITREV[256];
static void initrev(void){for(int i=0;i<256;i++){int b=i;b=((b&0xF0)>>4)|((b&0x0F)<<4);b=((b&0xCC)>>2)|((b&0x33)<<2);b=((b&0xAA)>>1)|((b&0x55)<<1);BITREV[i]=b;}}
/* out must have capacity n*9/8+16 ; returns output length */
long spc_cmp(const uint8_t* data,long n,uint8_t* out){
  initrev();
  long *head=malloc(sizeof(long)*65536); long *prev=malloc(sizeof(long)*(n+1));
  for(int i=0;i<65536;i++)head[i]=-1;
  long p=0,o=0;
  #define INS(pos) do{ if((pos)+2<=n){long q_=(pos); unsigned kk_=data[q_]|(data[q_+1]<<8); prev[q_]=head[kk_]; head[kk_]=q_;} }while(0)
  while(p<n){
    long fpos=o++; int flag=0;
    for(int bit=0;bit<8;bit++){
      if(p>=n)break;
      int best=0; long bpos=0;
      if(p+2<=n){
        unsigned k=data[p]|(data[p+1]<<8); long c=head[k]; int tries=0;
        long maxl=n-p; if(maxl>65)maxl=65;
        while(c>=0 && c>=p-1024 && tries<256){
          int l=2; while(l<maxl && data[c+l]==data[p+l]) l++;
          if(l>best){best=l;bpos=c; if(l==maxl)break;}
          c=prev[c]; tries++;
        }
      }
      if(best>=2){
        int off=(int)(bpos-p+1024); unsigned v=((best-2)<<10)|off;
        out[o++]=v&0xff; out[o++]=v>>8;
        for(int k=0;k<best;k++) INS(p+k);
        p+=best;
      } else {
        flag|=1<<bit; out[o++]=data[p]; INS(p); p++;
      }
    }
    out[fpos]=BITREV[flag];
  }
  free(head);free(prev);return o;
}

/* Scan compressed stream: returns position of last flag byte and number of tokens used in it (via out params).
   also returns decoded length. */
long spc_scan(const uint8_t* d,long n,long* last_flag_pos,int* used){
  initrev();
  long p=0,res=0; unsigned flag=1; long fpos=-1; int u=0;
  while(p<n){
    if(flag==1){ fpos=p; flag=0x100|BITREV[d[p]]; p++; u=0; if(p>=n)break; }
    if(flag&1){ p++; res++; }
    else { if(p+1>=n)break; unsigned b=d[p]|(d[p+1]<<8); p+=2; res+=(b>>10)+2; }
    u++; flag>>=1;
  }
  *last_flag_pos=fpos; *used=u; return res;
}
