import fs from "fs";
import { chunk } from "lodash";
import path from "path";
import { buildSitemapIndex, createSitemap } from "sitemap";

class SitemapGenerator {
  urls: [object?];
  chunks: object[][];
  sitemapSize: number;
  sitemapName: string;
  hostname: string;
  cacheTime: number;
  destinationDir: string;
  sitemaps: [string?];

  constructor(options) {
    this.sitemaps = [];
    this.urls = [];
    this.hostname = options.hostname;
    this.destinationDir = options.destinationDir || ".";
    this.sitemapName = options.sitemapName || "sitemap";
    this.sitemapSize = options.sitemapSize || 50000;
    this.cacheTime = options.cacheTime || 600000;
  }

  add(url: object) {
    this.urls.push(url);
  }

  generateSitemap(urls: [object?], filename: string) {
    this.sitemaps.push(filename);
    this.saveToFile(
      createSitemap({
        cacheTime: this.cacheTime,
        hostname: this.hostname,
        urls,
      }).toString(),
      filename
    );

    // tslint:disable-next-line: no-console
    console.log("DONE");
  }

  generateSitemapIndex(filename: string) {
    const urls = this.sitemaps.map(filename => `${this.hostname}/${filename}`);
    this.saveToFile(buildSitemapIndex({ urls }).toString(), filename);
  }

  saveToFile(data: string, filename: string) {
    fs.writeFileSync(path.join(this.destinationDir, filename), data);
  }

  generate(filename: string = "sitemap.xml") {
    this.chunks = chunk(this.urls, this.sitemapSize);

    if (this.chunks.length > 1) {
      this.chunks.forEach((chunk: [object], index) => {
        this.generateSitemap(chunk, `${this.sitemapName}-${index}.xml`);
      });
      this.generateSitemapIndex(filename);
    } else {
      this.generateSitemap(this.urls, filename);
    }
  }
}

export default SitemapGenerator;
