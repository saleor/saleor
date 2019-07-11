import * as React from "react";

import { maybe } from "../../core/utils";
import CachedImage from "./CachedImage";

import noPhotoImg from "../../images/no-photo.svg";

const CachedThumbnail: React.FC<{
  source: {
    thumbnail: { url: string; alt: string };
    thumbnail2x: { url: string };
  };
  noPhotoDefault?: boolean;
  children?: React.ReactNode;
}> = ({ source, noPhotoDefault, children }) => {
  const defaultImg = noPhotoDefault ? noPhotoImg : undefined;
  return (
    <CachedImage
      url={maybe(() => source.thumbnail.url, defaultImg)}
      url2x={maybe(() => source.thumbnail2x.url, defaultImg)}
      alt={maybe(() => source.thumbnail.alt, "")}
    >
      {children}
    </CachedImage>
  );
};

CachedThumbnail.defaultProps = {
  noPhotoDefault: true,
};

export default CachedThumbnail;
