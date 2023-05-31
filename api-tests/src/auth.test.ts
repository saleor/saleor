import { describe, expect, it } from "vitest";
import { makeClient } from "./utils";
import { gql } from "graphql-request";
import { TokenCreateMutation, TokenCreateMutationVariables } from "../generated/graphql";

const email = process.env.EMAIL || "";
const password = process.env.PASSWORD || "";

describe("testing authorization", () => {
  it("checks creating access tokens", async () => {
    const client = makeClient();
    const mutation = gql`
      mutation TokenCreate($email: String!, $password: String!) {
        tokenCreate(email: $email, password: $password) {
          csrfToken
          refreshToken
          token
          errors: accountErrors {
            ...AccountError
          }
          user {
            id
            email
          }
        }
      }
      fragment AccountError on AccountError {
        code
        field
        message
      }
    `;
    const result = await client.request<TokenCreateMutation, TokenCreateMutationVariables>(
      mutation,
      {
        email,
        password,
      }
    );

    expect(result.tokenCreate?.csrfToken).toBeTypeOf("string");
    expect(result.tokenCreate?.token).toBeTypeOf("string");
    expect(result.tokenCreate?.refreshToken).toBeTypeOf("string");
    expect(result.tokenCreate?.errors).toHaveLength(0);
  });
});
