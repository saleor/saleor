import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import PageList from "./";

const pageList = [
  {
    cursor: "12345678",
    node: {
      id: "abcd",
      isVisible: true,
      slug: "lorem-ipsum-dolor",
      title: "Lorem ipsum"
    }
  },
  {
    cursor: "12345678",
    node: {
      id: "abcde",
      isVisible: true,
      slug: "lorem-ipsum-consectetur",
      title: "Pellentesque habitant morbi tristique senectus"
    }
  },
  {
    cursor: "12345678",
    node: {
      id: "abcdef",
      isVisible: true,
      slug: "lorem-ipsum-amet",
      title: "Pellentesque metus turpis"
    }
  },
  {
    cursor: "12345678",
    node: {
      id: "abcdefg",
      isVisible: true,
      slug: "lorem-ipsum-sit",
      title: "Nulla blandit ut lectus at placerat"
    }
  }
];

describe("<PageList />", () => {
  it("renders while data is loading", () => {
    const component = renderer.create(
      <MemoryRouter>
        <PageList
          handlePreviousPage={jest.fn()}
          handleNextPage={jest.fn()}
          onEditClick={jest.fn()}
          onShowPageClick={jest.fn()}
          pageInfo={{
            endCursor: "",
            hasNextPage: false,
            hasPreviousPage: false,
            startCursor: ""
          }}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when data is fully loaded", () => {
    const component = renderer.create(
      <MemoryRouter>
        <PageList
          handlePreviousPage={jest.fn()}
          handleNextPage={jest.fn()}
          pages={pageList}
          onEditClick={jest.fn()}
          onShowPageClick={jest.fn()}
          pageInfo={{
            endCursor: "",
            hasNextPage: false,
            hasPreviousPage: false,
            startCursor: ""
          }}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when category list is empty", () => {
    const component = renderer.create(
      <MemoryRouter>
        <PageList
          handlePreviousPage={jest.fn()}
          handleNextPage={jest.fn()}
          pages={[]}
          onEditClick={jest.fn()}
          onShowPageClick={jest.fn()}
          pageInfo={{
            endCursor: "",
            hasNextPage: false,
            hasPreviousPage: false,
            startCursor: ""
          }}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
});
