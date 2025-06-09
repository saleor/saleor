from django.test import TestCase
from django.contrib.auth import get_user_model
from saleor.product.models import Product, ProductBrowsingHistory
from saleor.graphql.tests.utils import get_graphql_content

User = get_user_model()

class TestBrowsingHistoryGraphQL(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='testpass123'
)
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price_amount=100
        )
        self.client.login(email='test@example.com', password='testpass123')

    def test_my_browsing_history_query(self):
        """Test querying browsing history"""
        # Record browsing history
        ProductBrowsingHistory.record_view(
            product=self.product,
            user=self.user
        )
        
        query = '''
        query {
            myBrowsingHistory(first: 10) {
                edges {
                    node {
                        id
                        viewedAt
                        product {
                            id
                            name
                        }
                    }
                }
            }
        }
        '''
        
        response = self.client.post(
            "/graphql/",
            data={"query": query},
            content_type="application/json"
        )
        content = get_graphql_content(response)
        edges = content["data"]["myBrowsingHistory"]["edges"]
        
        assert len(edges) == 1
        node = edges[0]["node"]
        assert node["product"]["name"] == "Test Product"
        assert node["viewedAt"] is not None

    def test_record_product_view_mutation(self):
        """Test recording product view via mutation"""
        mutation = '''
        mutation recordView($productId: ID!) {
            recordProductView(productId: $productId) {
                browsingHistory {
                    id
                    viewedAt
                    product {
                        id
                        name
                    }
                }
            }
        }
        '''
        
        product_global_id = f"Product:{self.product.pk}"
        
        response = self.client.post(
            "/graphql/",
            data={
                "query": mutation,
                "variables": {"productId": product_global_id}
            },
            content_type="application/json"
        )
        
        content = get_graphql_content(response)
        browsing_history = content["data"]["recordProductView"]["browsingHistory"]
        
        assert browsing_history is not None
        assert browsing_history["product"]["name"] == "Test Product"
        assert browsing_history["viewedAt"] is not None
