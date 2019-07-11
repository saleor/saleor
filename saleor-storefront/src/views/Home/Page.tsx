import "./scss/index.scss";

import classNames from "classnames";
import * as React from "react";
import { Link } from "react-router-dom";

import { Button, Loader, ProductsFeatured } from "../../components";
import { ProductsList_categories } from "../../core/types/saleor";
import { generateCategoryUrl } from "../../core/utils";
import {
  ProductsList_shop,
  ProductsList_shop_homepageCollection_backgroundImage
} from "./types/ProductsList";

import { structuredData } from "../../core/SEO/Homepage/structuredData";

import noPhotoImg from "../../images/no-photo.svg";

const Page: React.FC<{
  loading: boolean;
  categories: ProductsList_categories;
  backgroundImage: ProductsList_shop_homepageCollection_backgroundImage;
  shop: ProductsList_shop;
}> = ({ loading, categories, backgroundImage, shop }) => (
  <>
    <script className="structured-data-list" type="application/ld+json">
      {structuredData(shop)}
    </script>
    <div
      className="home-page__hero"
      style={
        backgroundImage
          ? { backgroundImage: `url(${backgroundImage.url})` }
          : null
      }
    >
      <div className="home-page__hero-text">
        <div>
          <span className="home-page__hero__title">
            <h1>Final reduction</h1>
          </span>
        </div>
        <div>
          <span className="home-page__hero__title">
            <h1>Up to 70% off sale</h1>
          </span>
        </div>
      </div>
      <div className="home-page__hero-action">
        {loading && !categories ? (
          <Loader />
        ) : (
          <Link
            to={generateCategoryUrl(
              categories.edges[0].node.id,
              categories.edges[0].node.name
            )}
          >
            <Button>Shop sale</Button>
          </Link>
        )}
      </div>
    </div>
    <ProductsFeatured />
    <div className="home-page__categories">
      <div className="container">
        <h3>Shop by category</h3>
        <div className="home-page__categories__list">
          {categories.edges.map(({ node: category }) => (
            <div key={category.id}>
              <Link
                to={generateCategoryUrl(category.id, category.name)}
                key={category.id}
              >
                <div
                  className={classNames("home-page__categories__list__image", {
                    "home-page__categories__list__image--no-photo": !category.backgroundImage,
                  })}
                  style={{
                    backgroundImage: `url(${
                      category.backgroundImage
                        ? category.backgroundImage.url
                        : noPhotoImg
                    })`,
                  }}
                />
                <h3>{category.name}</h3>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  </>
);

export default Page;
