export const xsBreakpoint = 576;
export const smBreakpoint = 768;
export const mdBreakpoint = 992;
export const lgBreakpoint = 1200;

export const isMobile = () => {
  	if(window.innerWidth < smBreakpoint) {
  		return true;
  	} else {
  		return false;
  	}
}

export const isTablet = () => {
  	if(window.innerWidth >= smBreakpoint && window.innerWidth <= mdBreakpoint) {
  		return true;
  	} else {
  		return false;
  	}
}