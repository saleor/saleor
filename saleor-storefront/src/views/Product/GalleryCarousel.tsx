import * as React from "react";

import { CachedImage, Carousel } from "../../components/";
import { ProductDetails_product_images } from "./types/ProductDetails";

import noPhotoImg from "../../images/no-photo.svg";

const GalleryCarousel: React.FC<{
  images: ProductDetails_product_images[];
}> = ({ images }) => (
  <div className="product-page__product__gallery">
    <Carousel
      renderCenterLeftControls={() => null}
      renderCenterRightControls={() => null}
      renderBottomCenterControls={props => {
        const indexes = [];

        for (let i = 0; i < props.slideCount; i++) {
          indexes.push(i);
        }

        return (
          <ul className="product-page__product__gallery__nav">
            {indexes.map(index => (
              <li
                key={index}
                onClick={props.goToSlide.bind(null, index)}
                className={props.currentSlide === index ? "active" : ""}
              >
                <span />
              </li>
            ))}
          </ul>
        );
      }}
    >
      {images.map(image => (
        <CachedImage url={image.url || noPhotoImg} key={image.id}>
          <img src={noPhotoImg} />
        </CachedImage>
      ))}
    </Carousel>
  </div>
);

export default GalleryCarousel;
