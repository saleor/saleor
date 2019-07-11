import * as React from "react";

interface CachedImageProps {
  url: string;
  url2x?: string;
  alt?: string;
}

interface CachedImageState {
  online: boolean;
  isUnavailable: boolean;
}

class CachedImage extends React.Component<CachedImageProps, CachedImageState> {
  state: CachedImageState = {
    isUnavailable: false,
    online: "onLine" in navigator ? navigator.onLine : true,
  };

  updateOnlineStatus = () => {
    this.setState({ online: navigator.onLine });
  };

  async updateAvailability() {
    const { url, url2x } = this.props;
    let isUnavailable = false;
    if ("caches" in window) {
      if (!this.state.online) {
        const match = await window.caches.match(url);
        let match2x;
        if (url2x) {
          match2x = await window.caches.match(url2x);
        }
        if (!match && !match2x) {
          isUnavailable = true;
        }
      }
    }
    if (this.state.isUnavailable !== isUnavailable) {
      this.setState({ isUnavailable });
    }
  }

  addImagesToCache() {
    if ("caches" in window) {
      const { url, url2x } = this.props;
      window.caches
        .open("image-cache")
        .then(cache => cache.addAll([url, url2x]));
    }
  }

  componentDidMount() {
    addEventListener("offline", this.updateOnlineStatus);
    addEventListener("online", this.updateOnlineStatus);
    this.updateAvailability();
  }

  componentWillUnmount() {
    removeEventListener("offline", this.updateOnlineStatus);
    removeEventListener("online", this.updateOnlineStatus);
  }

  componentDidUpdate() {
    this.updateAvailability();
  }

  render() {
    const { url, url2x, alt } = this.props;
    if (this.state.isUnavailable) {
      return this.props.children || null;
    }
    return (
      <img
        src={url}
        srcSet={url2x ? `${url} 1x, ${url2x} 2x` : `${url} 1x`}
        alt={alt}
      />
    );
  }
}

export default CachedImage;
