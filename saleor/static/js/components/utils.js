export const xsBreakpoint = 576;
export const smBreakpoint = 768;
export const mdBreakpoint = 992;
export const lgBreakpoint = 1200;

export const isMobile = () => {
  	return window.innerWidth < smBreakpoint;
}

export const isTablet = () => {
  	return window.innerWidth >= smBreakpoint && window.innerWidth <= mdBreakpoint;
}

export const getReleaseListColumnNumber = () => {
  if (window.innerWidth < xsBreakpoint) {
    return 1
  } else if (window.innerWidth < smBreakpoint) {
    return 3
  } else if (window.innerWidth < mdBreakpoint) {
    return 4
  } else {
    return 6
  }
}
