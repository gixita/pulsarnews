def security(test_client):
    security_admin_panel(test_client)
    security_posts_from_other_companies(test_client)

def security_posts_from_other_companies(test_client):
    pass

def security_admin_panel(test_client):
    response = test_client.get('/admin',
                                follow_redirects=True)
    assert b'Super admin panel' not in response.data
    
    response = test_client.get('/admin/users',
                                follow_redirects=True)
    assert b'Super admin panel' not in response.data
    
    response = test_client.get('/admin/companies',
                                follow_redirects=True)
    assert b'Super admin panel' not in response.data
    
    response = test_client.get('/admin/domains',
                                follow_redirects=True)
    assert b'Super admin panel' not in response.data
    
    response = test_client.get('/admin/posts',
                                follow_redirects=True)
    assert b'Super admin panel' not in response.data