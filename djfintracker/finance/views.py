from django.shortcuts import render, redirect, HttpResponse
from django.views import View
from finance.forms import RegisterForm, TransactionForm, GoalForm
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Transaction, Goal
from django.db.models import Sum
from .admin import TransactionResource
from django.contrib import messages

class RegisterView(View):
  def get(self, request, *args, **kwargs):
    form = RegisterForm()
    return render(request, 'finance/register.html', {'form':form})
  
  def post(self, request, *args, **kwargs):
    form = RegisterForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      messages.success(request, 'Account created successfully!')
      return redirect('dashboard')
    return render(request, 'finance/register.html', {'form':form})

class DashboardView(LoginRequiredMixin, View):
  def get(self, request, *args, **kwargs):
    transactions = Transaction.objects.filter(user = request.user)
    goals = Goal.objects.filter(user = request.user)

    # Calculate total income and expenses
    total_income = Transaction.objects.filter(user = request.user, transaction_type='Income').aggregate(Sum('amount'))['amount__sum'] or 0

    total_expense = Transaction.objects.filter(user = request.user, transaction_type='Expense').aggregate(Sum('amount'))['amount__sum'] or 0

    net_savings = total_income - total_expense

    remaining_savings = net_savings

    goal_progress = []
    for goal in goals:
      if remaining_savings >= goal.target_amount:
        goal_progress.append({'goal':goal, 'progress': 100})
        remaining_savings -= goal.target_amount
      elif remaining_savings > 0:
        progress = (remaining_savings / goal.target_amount) * 100
        goal_progress.append({'goal': goal, 'progress': progress})
        remaining_savings = 0
      else:
        goal_progress.append({'goal': goal, 'progress': 0})

    context = {
      'transactions': transactions,
      'total_income': total_income,
      'total_expense': total_expense,
      'net_savings': net_savings,
      'goal_progress': goal_progress,
    }
    return render(request, 'finance/dashboard.html', context)
  
class TransactionCreateView(LoginRequiredMixin, View):
  def get(self, request, *args, **kwargs):
    form = TransactionForm()
    return render(request, 'finance/transaction_form.html', {'form':form})
  
  def post(self, request, *args, **kwargs):
    form = TransactionForm(request.POST)
    if form.is_valid():
      transaction = form.save(commit=False)
      transaction.user = request.user
      transaction.save()
      messages.success(request, 'Transaction added successfully!')
      return redirect('dashboard')
    return render(request, 'finance/transaction_form.html', {'form':form})
  
class TransactionListView(LoginRequiredMixin, View):
  def get(self, request, *args, **kwargs):
    transactions = Transaction.objects.filter(user = request.user)
    return render(request, 'finance/transaction_list.html', {'transactions':transactions})
  
class GoalCreateView(LoginRequiredMixin, View):
  def get(self, request, *args, **kwargs):
    form = GoalForm()
    return render(request, 'finance/goal_form.html', {'form':form})
  
  def post(self, request, *args, **kwargs):
    form = GoalForm(request.POST)
    if form.is_valid():
      goal = form.save(commit=False)
      goal.user = request.user
      goal.save()
      messages.success(request, 'Goal created successfully!')
      return redirect('dashboard')
    return render(request, 'finance/goal_form.html', {'form':form})
  
def export_transactions(request):
  user_transactions = Transaction.objects.filter(user = request.user)

  transactions_resource = TransactionResource()
  dataset = transactions_resource.export(queryset=user_transactions)

  excel_data = dataset.export('xlsx')

  # Create an HttpResponse with the correct MIME type for an Excel file
  response = HttpResponse(excel_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

  # Set the header for downloading the file
  response['Content-Disposition'] = 'attachment; filename=transactions_report.xlsx'
  return response





# this is crud operation code from chatgpt------------------------------------------------------------

# ---------------- GOAL CRUD OPERATIONS ----------------

# from django.shortcuts import get_object_or_404

# # Goal List View
# class GoalListView(LoginRequiredMixin, View):
#     def get(self, request, *args, **kwargs):
#         goals = Goal.objects.filter(user=request.user)
#         return render(request, 'finance/goal_list.html', {'goals': goals})


# # Goal Update View
# class GoalUpdateView(LoginRequiredMixin, View):
#     def get(self, request, pk, *args, **kwargs):
#         goal = get_object_or_404(Goal, pk=pk, user=request.user)
#         form = GoalForm(instance=goal)
#         return render(request, 'finance/goal_form.html', {'form': form, 'edit_mode': True})

#     def post(self, request, pk, *args, **kwargs):
#         goal = get_object_or_404(Goal, pk=pk, user=request.user)
#         form = GoalForm(request.POST, instance=goal)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Goal updated successfully!')
#             return redirect('goal_list')
#         return render(request, 'finance/goal_form.html', {'form': form, 'edit_mode': True})


# # Goal Delete View
# class GoalDeleteView(LoginRequiredMixin, View):
#     def post(self, request, pk, *args, **kwargs):
#         goal = get_object_or_404(Goal, pk=pk, user=request.user)
#         goal.delete()
#         messages.success(request, 'Goal deleted successfully!')
#         return redirect('goal_list')


#----------------------------------------------------Encapsulate----------------------------------------



from django.urls import reverse_lazy
from django.views.generic import UpdateView, DeleteView
from .models import Goal

class GoalUpdateView(UpdateView):
    model = Goal
    fields = ['title', 'target_amount', 'deadline']
    template_name = 'finance/goal_form.html'
    success_url = reverse_lazy('goal_add')  # redirect to goal list or dashboard

class GoalDeleteView(DeleteView):
    model = Goal
    template_name = 'finance/goal_confirm_delete.html'
    success_url = reverse_lazy('goal_add')


class DashboardView(UpdateView):
    template_name = 'finance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['goals'] = Goal.objects.all()  # make sure this returns saved goals
        return context





