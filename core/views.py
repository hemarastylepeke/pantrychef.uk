from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
from .models import UserPantry, Ingredient, ConsumptionRecord, FoodWasteRecord, ImageProcessingJob, Recipe
from .forms import PantryItemForm, ManualIngredientForm, ConsumptionForm, WasteRecordForm
from .services.vision_service import ExpiryDateDetector
from accounts.models import Budget

@login_required(login_url='account_login')
def pantry_dashboard_view(request):
    """
    Main pantry dashboard showing current inventory and alerts
    """
    # Get user's pantry items
    pantry_items = UserPantry.objects.filter(user=request.user, status='active').order_by('expiry_date')
    
    # Get items expiring soon (within 3 days)
    soon = timezone.now().date() + timedelta(days=3)
    expiring_soon = pantry_items.filter(expiry_date__lte=soon)
    
    # Add days until expiry for template
    for item in expiring_soon:
        item.days_until_expiry = (item.expiry_date - timezone.now().date()).days
    
    # Get recently expired items
    expired_items = pantry_items.filter(expiry_date__lt=timezone.now().date())
    
    # Get consumption history (last 7 days)
    recent_consumption = ConsumptionRecord.objects.filter(
        user=request.user, 
        date_consumed__gte=timezone.now().date() - timedelta(days=7)
    ).select_related('pantry_item', 'recipe').order_by('-date_consumed')[:10]
    
    # Calculate pantry statistics
    total_items = pantry_items.count()
    total_value = sum(item.price for item in pantry_items if item.price)
    
    # Calculate waste savings (you'll need to implement this logic)
    waste_savings = calculate_waste_savings(request.user)
    
    # Recipe suggestions (you'll need to implement this logic)
    recipe_suggestions = get_recipe_suggestions(request.user)
    
    # Waste reduction tips
    waste_tips = [
        "Freeze leftover bread to use for croutons or breadcrumbs.",
        "Use vegetable scraps to make homemade broth.",
        "Plan meals around ingredients that will expire soon.",
        "Store herbs in water to keep them fresh longer.",
        "Use overripe fruits in smoothies or baking."
    ]
    
    # Budget information
    current_budget = Budget.objects.filter(user=request.user, active=True).first()
    budget_percentage = 0
    if current_budget:
        # Calculate budget usage (you'll need to implement this)
        budget_percentage = min(100, int((current_budget.amount_spent / current_budget.amount) * 100))
    
    context = {
        'pantry_items': pantry_items,
        'expiring_soon': expiring_soon,
        'expired_items': expired_items,
        'recent_consumption': recent_consumption,
        'total_items': total_items,
        'total_value': total_value,
        'waste_savings': waste_savings,
        'waste_reduction_percentage': 24,  # You'll need to calculate this
        'recipes_created': Recipe.objects.filter(created_by=request.user).count(),
        'pantry_utilization': 85,  # You'll need to calculate this
        'current_budget': current_budget,
        'budget_percentage': budget_percentage,
        'recipe_suggestions': recipe_suggestions,
        'waste_tips': waste_tips,
        'pantry_form': PantryItemForm(),
        'manual_form': ManualIngredientForm(),
    }
    return render(request, 'core/pantry_dashboard.html', context)

# Helper functions you'll need to implement
def calculate_waste_savings(user):
    """Calculate total waste savings for the user"""
    # Implement your logic here
    return 156  # Example value

def get_recipe_suggestions(user):
    """Get AI-powered recipe suggestions based on pantry items"""
    # Implement your logic here
    return [
        {
            'name': 'Veggie Omelette',
            'matching_ingredients': ['eggs', 'spinach', 'tomatoes'],
            'match_percentage': 95,
            'prep_time': 15,
            'calories': 320,
            'rating': 4.5
        },
        {
            'name': 'Pasta Pomodoro', 
            'matching_ingredients': ['pasta', 'tomatoes', 'basil'],
            'match_percentage': 88,
            'prep_time': 25,
            'calories': 450,
            'rating': 4.2
        }
    ]

@login_required(login_url='account_login')
def add_pantry_item_view(request):
    """
    Add new item to pantry via form
    """
    if request.method == 'POST':
        form = PantryItemForm(request.POST, request.FILES)
        if form.is_valid():
            pantry_item = form.save(commit=False)
            pantry_item.user = request.user
            
            # Handle image uploads
            if 'product_image' in request.FILES:
                pantry_item.product_image = request.FILES['product_image']
            if 'expiry_label_image' in request.FILES:
                pantry_item.expiry_label_image = request.FILES['expiry_label_image']
            
            pantry_item.save()
            messages.success(request, f'{pantry_item.ingredient.name} added to pantry!')
            return redirect('pantry_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PantryItemForm()
    
    context = {
        'form': form,
        'ingredients': Ingredient.objects.all().order_by('name')
    }
    return render(request, 'core/add_pantry_item.html', context)

@login_required(login_url='account_login')
def add_manual_ingredient_view(request):
    """
    Add custom ingredient manually (not in database)
    """
    if request.method == 'POST':
        form = ManualIngredientForm(request.POST)
        if form.is_valid():
            # Create or get ingredient
            ingredient_name = form.cleaned_data['name']
            ingredient, created = Ingredient.objects.get_or_create(
                name=ingredient_name.lower(),
                defaults={
                    'category': form.cleaned_data['category'],
                    'typical_expiry_days': form.cleaned_data['typical_expiry_days']
                }
            )
            
            # Create pantry item
            pantry_item = UserPantry(
                user=request.user,
                ingredient=ingredient,
                custom_name=form.cleaned_data['custom_name'] or ingredient_name,
                quantity=form.cleaned_data['quantity'],
                unit=form.cleaned_data['unit'],
                purchase_date=form.cleaned_data['purchase_date'],
                expiry_date=form.cleaned_data['expiry_date'],
                price=form.cleaned_data['price'],
                detection_source='manual'
            )
            pantry_item.save()
            
            messages.success(request, f'{ingredient_name} added to pantry!')
            return redirect('core:pantry_dashboard')
    else:
        form = ManualIngredientForm()
    
    context = {'form': form}
    return render(request, 'core/add_manual_ingredient.html', context)

@login_required(login_url='account_login')
def scan_ingredient_view(request):
    """
    Handle image upload for ingredient scanning
    """
    if request.method == 'POST':
        if 'image' in request.FILES:
            # Create image processing job
            image_file = request.FILES['image']
            job = ImageProcessingJob.objects.create(
                user=request.user,
                image=image_file,
                job_type='expiry'
            )
            
            # In a real implementation, this would be handled by Celery
            # For now, we'll process synchronously
            try:
                
                detector = ExpiryDateDetector()
                result = detector.detect_expiry_date(image_file.temporary_file_path())
                
                job.status = 'completed'
                job.detected_text = result.get('detected_text', '')
                job.processed_data = result
                job.processed_at = timezone.now()
                job.save()
                
                return JsonResponse({
                    'success': True,
                    'job_id': job.id,
                    'result': result
                })
                
            except Exception as e:
                job.status = 'failed'
                job.error_message = str(e)
                job.save()
                return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'core/scan_ingredient.html')

@login_required(login_url='account_login')
def edit_pantry_item(request, item_id):
    """
    Edit existing pantry item
    """
    pantry_item = get_object_or_404(UserPantry, id=item_id, user=request.user)
    
    if request.method == 'POST':
        form = PantryItemForm(request.POST, request.FILES, instance=pantry_item)
        if form.is_valid():
            form.save()
            messages.success(request, f'{pantry_item.ingredient.name} updated successfully!')
            return redirect('core:pantry_dashboard')
    else:
        form = PantryItemForm(instance=pantry_item)
    
    context = {
        'form': form,
        'pantry_item': pantry_item
    }
    return render(request, 'core/edit_pantry_item.html', context)

@login_required(login_url='account_login')
def update_quantity(request, item_id):
    """
    AJAX view to update item quantity
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        pantry_item = get_object_or_404(UserPantry, id=item_id, user=request.user)
        new_quantity = request.POST.get('quantity')
        
        try:
            pantry_item.quantity = float(new_quantity)
            pantry_item.save()
            
            return JsonResponse({
                'success': True,
                'new_quantity': pantry_item.quantity,
                'item_name': pantry_item.ingredient.name
            })
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid quantity'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required(login_url='account_login')
def log_consumption_view(request, item_id):
    """
    Log consumption of a pantry item
    """
    pantry_item = get_object_or_404(UserPantry, id=item_id, user=request.user)
    
    if request.method == 'POST':
        form = ConsumptionForm(request.POST)
        if form.is_valid():
            quantity_used = form.cleaned_data['quantity_used']
            recipe = form.cleaned_data.get('recipe')
            notes = form.cleaned_data.get('notes', '')
            
            # Update pantry item quantity
            if quantity_used >= pantry_item.quantity:
                # Used all of it
                pantry_item.quantity = 0
                pantry_item.status = 'consumed'
            else:
                pantry_item.quantity -= quantity_used
            
            pantry_item.save()
            
            # Create consumption record
            consumption = ConsumptionRecord.objects.create(
                user=request.user,
                pantry_item=pantry_item,
                recipe=recipe,
                quantity_used=quantity_used,
                notes=notes
            )
            
            messages.success(request, f'Consumption of {pantry_item.ingredient.name} logged!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('core:pantry_dashboard')
    else:
        form = ConsumptionForm(initial={'quantity_used': pantry_item.quantity})
    
    context = {
        'form': form,
        'pantry_item': pantry_item
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'html': render(request, 'core/consumption_modal.html', context).content.decode()
        })
    
    return render(request, 'core/log_consumption.html', context)

@login_required(login_url='account_login')
def record_waste(request, item_id):
    """
    Record food waste for a pantry item
    """
    pantry_item = get_object_or_404(UserPantry, id=item_id, user=request.user)
    
    if request.method == 'POST':
        form = WasteRecordForm(request.POST)
        if form.is_valid():
            quantity_wasted = form.cleaned_data['quantity_wasted']
            reason = form.cleaned_data['reason']
            reason_details = form.cleaned_data.get('reason_details', '')
            
            # Create waste record
            waste_record = FoodWasteRecord.objects.create(
                user=request.user,
                ingredient=pantry_item.ingredient,
                original_quantity=pantry_item.quantity,
                quantity_wasted=quantity_wasted,
                unit=pantry_item.unit,
                cost=pantry_item.price if pantry_item.price else 0,
                reason=reason,
                reason_details=reason_details,
                purchase_date=pantry_item.purchase_date,
                expiry_date=pantry_item.expiry_date
            )
            
            # Update pantry item
            if quantity_wasted >= pantry_item.quantity:
                pantry_item.quantity = 0
                pantry_item.status = 'wasted'
            else:
                pantry_item.quantity -= quantity_wasted
            
            pantry_item.save()
            
            messages.warning(request, f'Waste recorded for {pantry_item.ingredient.name}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('core:pantry_dashboard')
    else:
        form = WasteRecordForm(initial={
            'quantity_wasted': pantry_item.quantity,
            'reason': 'expired'
        })
    
    context = {
        'form': form,
        'pantry_item': pantry_item
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'html': render(request, 'core/waste_modal.html', context).content.decode()
        })
    
    return render(request, 'core/record_waste.html', context)

@login_required(login_url='account_login')
def delete_pantry_item(request, item_id):
    """
    Remove item from pantry (soft delete)
    """
    pantry_item = get_object_or_404(UserPantry, id=item_id, user=request.user)
    
    if request.method == 'POST':
        pantry_item.status = 'consumed'  # or 'wasted' based on context
        pantry_item.save()
        messages.success(request, f'{pantry_item.ingredient.name} removed from pantry!')
        return redirect('core:pantry_dashboard')
    
    context = {'pantry_item': pantry_item}
    return render(request, 'core/delete_pantry_item.html', context)

@login_required(login_url='account_login')
def pantry_analytics_view(request):
    """
    Show pantry analytics and waste statistics
    """
    # Waste statistics
    waste_records = FoodWasteRecord.objects.filter(user=request.user).order_by('-waste_date')[:20]
    
    # Calculate waste metrics
    total_waste_cost = sum(record.cost for record in waste_records)
    waste_by_reason = {}
    for record in waste_records:
        reason = record.get_reason_display()
        waste_by_reason[reason] = waste_by_reason.get(reason, 0) + record.cost
    
    # Consumption patterns
    consumption_records = ConsumptionRecord.objects.filter(user=request.user).order_by('-date_consumed')[:50]
    
    # Current pantry value
    current_pantry = UserPantry.objects.filter(user=request.user, status='active')
    current_value = sum(item.price for item in current_pantry if item.price)
    
    context = {
        'waste_records': waste_records,
        'total_waste_cost': total_waste_cost,
        'waste_by_reason': waste_by_reason,
        'consumption_records': consumption_records,
        'current_pantry_value': current_value,
    }
    return render(request, 'core/pantry_analytics.html', context)

@login_required(login_url='account_login')
def expiring_soon_api(request):
    """
    API endpoint for items expiring soon
    """
    soon = timezone.now().date() + timedelta(days=3)
    expiring_items = UserPantry.objects.filter(
        user=request.user, 
        status='active',
        expiry_date__lte=soon
    ).order_by('expiry_date')
    
    items_data = []
    for item in expiring_items:
        items_data.append({
            'id': item.id,
            'name': item.ingredient.name,
            'expiry_date': item.expiry_date.isoformat(),
            'quantity': item.quantity,
            'unit': item.unit,
            'days_until_expiry': (item.expiry_date - timezone.now().date()).days
        })
    
    return JsonResponse({'expiring_items': items_data})

@login_required(login_url='account_login')
def quick_consume(request, item_id):
    """
    Quick consumption without form (for simple use cases)
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        pantry_item = get_object_or_404(UserPantry, id=item_id, user=request.user)
        
        # Mark as fully consumed
        ConsumptionRecord.objects.create(
            user=request.user,
            pantry_item=pantry_item,
            quantity_used=pantry_item.quantity,
            notes='Quick consumption'
        )
        
        pantry_item.quantity = 0
        pantry_item.status = 'consumed'
        pantry_item.save()
        
        return JsonResponse({'success': True, 'message': 'Item consumed!'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})